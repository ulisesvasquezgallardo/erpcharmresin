from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Header
from sqlalchemy.orm import Session
import pandas as pd
import io
import datetime

from database import get_db
# Importamos los modelos
from models.models import Product, InventoryLog, Client, Order, OrderDetail, Combo, ComboComponent

from pydantic import BaseModel

router = APIRouter()


# 1. RUTA PARA CREAR ÓRDENES DE VENTA (SOPORTA PRODUCTOS Y COMBOS)
@router.post("/orders/")
def create_order(
        payload: dict,
        x_user_role: str = Header(None),
        db: Session = Depends(get_db)
):
    if x_user_role != "VENDEDOR":
        raise HTTPException(status_code=403, detail="Acceso denegado: Solo los Vendedores pueden registrar compras.")

    items = payload.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="El carrito no puede estar vacío.")

    try:
        # 1. Buscar o crear al Cliente
        client_data = payload.get("client", {})
        doc_number = client_data.get("document_number")

        client = db.query(Client).filter(Client.document_number == doc_number).first()
        if not client:
            client = Client(
                doc_type=client_data.get("doc_type"),
                document_number=doc_number,
                name=client_data.get("name")
            )
            db.add(client)
            db.flush()

        # 2. Fechas
        est_date_str = payload.get("est_delivery_date")
        est_date_obj = datetime.datetime.strptime(est_date_str, "%Y-%m-%d").date()

        # 3. Cabecera de la Orden
        new_order = Order(
            client_id=client.id,
            delivery_type=payload.get("delivery_type"),
            district=payload.get("district"),
            address=payload.get("address"),
            est_delivery_date=est_date_obj,
            total_amount=0.0
        )
        db.add(new_order)
        db.flush()

        total_order_amount = 0.0

        # 4. Procesar Carrito
        for item in items:
            if item.get("item_type") == "PRODUCTO":
                product = db.query(Product).filter(Product.id == item["item_id"]).first()
                if not product:
                    db.rollback()
                    raise HTTPException(status_code=404, detail=f"Producto con ID {item['item_id']} no encontrado.")
                if product.stock < item["quantity"]:
                    db.rollback()
                    raise HTTPException(status_code=400, detail=f"Stock insuficiente para {product.name}.")

                product.stock -= item["quantity"]
                unit_price = product.unit_price

            elif item.get("item_type") == "COMBO":
                combo = db.query(Combo).filter(Combo.id == item["item_id"]).first()
                if not combo:
                    db.rollback()
                    raise HTTPException(status_code=404, detail=f"Combo con ID {item['item_id']} no encontrado.")

                unit_price = 0.0
                # Descontar stock real de los componentes del combo
                for component in combo.components:
                    base_product = component.product
                    required_qty = component.quantity * item["quantity"]

                    if base_product.stock < required_qty:
                        db.rollback()
                        raise HTTPException(status_code=400,
                                            detail=f"Stock insuficiente de '{base_product.name}' para armar el {combo.name}.")

                    base_product.stock -= required_qty
                    unit_price += (base_product.unit_price * component.quantity)

            # Sumar al subtotal
            line_total = unit_price * item["quantity"]
            total_order_amount += line_total

            # Crear registro individual
            order_detail = OrderDetail(
                order_id=new_order.id,
                item_type=item["item_type"],
                item_id=item["item_id"],
                quantity=item["quantity"],
                unit_price=unit_price
            )
            db.add(order_detail)

        # 5. Consolidar la Orden
        new_order.total_amount = total_order_amount
        db.commit()

        return {"status": "success", "order_id": new_order.id, "total_amount": total_order_amount,
                "detail": "Venta guardada."}

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


# 2. RUTA DE CATÁLOGO UNIFICADO
@router.get("/catalog/")
def get_catalog(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    catalog = [{"id": p.id, "sku": p.sku, "name": p.name, "stock": p.stock, "unit_price": p.unit_price,
                "item_type": "PRODUCTO"} for p in products]

    combos = db.query(Combo).all()
    for c in combos:
        combo_price = 0.0
        max_combos_possible = float('inf')

        for comp in c.components:
            prod = comp.product
            combo_price += prod.unit_price * comp.quantity
            possible = prod.stock // comp.quantity
            if possible < max_combos_possible:
                max_combos_possible = possible

        if max_combos_possible == float('inf'):
            max_combos_possible = 0

        catalog.append({
            "id": c.id,
            "sku": c.sku,
            "name": f"📦 COMBO: {c.name}",
            "stock": int(max_combos_possible),
            "unit_price": combo_price,
            "item_type": "COMBO"
        })

    return catalog


# 3. CARGA Y ACTUALIZACIÓN MASIVA DESDE EXCEL
@router.post("/inventory/upload-excel/")
async def upload_excel_inventory(
        file: UploadFile = File(...),
        x_user_role: str = Header(None),
        db: Session = Depends(get_db)
):
    if x_user_role != "ALMACEN":
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx o .xls)")

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        # PROTECCIÓN: Limpiar filas vacías o datos corruptos
        df = df.dropna(subset=['sku', 'name'])
        df['stock'] = df['stock'].fillna(0)
        df['unit_price'] = df['unit_price'].fillna(0.0)

        required_columns = ['sku', 'name', 'stock', 'unit_price']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400,
                                detail="El Excel debe contener las columnas: sku, name, stock, unit_price")

        created = 0
        updated = 0

        for index, row in df.iterrows():
            sku_val = str(row['sku']).strip()
            name_val = str(row['name']).strip()
            stock_val = int(row['stock'])
            price_val = float(row['unit_price'])

            if stock_val < 0 or price_val < 0:
                continue

            product = db.query(Product).filter(Product.sku == sku_val).first()
            if product:
                old_stock = product.stock
                if old_stock != stock_val:
                    product.stock = stock_val
                    product.unit_price = price_val
                    db.add(InventoryLog(product_sku=sku_val, old_stock=old_stock, new_stock=stock_val, reason="Excel"))
                    updated += 1
            else:
                new_product = Product(sku=sku_val, name=name_val, stock=stock_val, unit_price=price_val)
                db.add(new_product)
                db.add(InventoryLog(product_sku=sku_val, old_stock=0, new_stock=stock_val, reason="Nueva Creación"))
                created += 1

        db.commit()
        return {"status": "success", "detail": f"Creados: {created}, Actualizados: {updated}."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# 4. AUTENTICACIÓN
class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/auth/login/")
def login(credentials: LoginRequest):
    if credentials.username == "vendedor1" and credentials.password == "clave123":
        return {"status": "success", "username": "vendedor1", "role": "VENDEDOR"}
    elif credentials.username == "jefe1" and credentials.password == "clave456":
        return {"status": "success", "username": "jefe1", "role": "ALMACEN"}
    else:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")


# 5. RUTA SECRETA PARA CREAR UN COMBO DE PRUEBA
@router.post("/debug/seed-combo/")
def create_test_combo(db: Session = Depends(get_db)):
    """Ejecuta esta ruta una vez para crear un combo de prueba con los productos existentes."""
    try:
        products = db.query(Product).limit(2).all()
        if len(products) < 2:
            return {"error": "Sube al menos 2 productos en tu Excel antes de crear un combo."}

        test_combo = Combo(sku="CMB-001", name="Kit Básico Odontológico")
        db.add(test_combo)
        db.flush()

        db.add(ComboComponent(combo_id=test_combo.id, product_id=products[0].id, quantity=2))
        db.add(ComboComponent(combo_id=test_combo.id, product_id=products[1].id, quantity=1))

        db.commit()
        return {"msg": "Combo de prueba creado exitosamente!"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}


# 6. RUTA PARA EL PANEL DE REPORTES (EDICIÓN EJECUTIVA OPTIMIZADA)
@router.get("/reports/sales/")
def get_sales_report(x_user_role: str = Header(None), db: Session = Depends(get_db)):
    if x_user_role != "ALMACEN":
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo Jefatura puede ver el Dashboard.")

    orders = db.query(Order).order_by(Order.id.asc()).all()
    details = db.query(OrderDetail).all()

    total_revenue = 0.0
    history = []

    for o in orders:
        total_revenue += o.total_amount
        client_name = o.client.name if o.client else "Cliente General"

        # Guardamos la fecha en formato ISO estándar para que el frontend la agrupe fácilmente
        formatted_date = o.est_delivery_date.strftime("%Y-%m-%d") if isinstance(o.est_delivery_date, (datetime.date,
                                                                                                      datetime.datetime)) else str(
            o.est_delivery_date)

        history.append({
            "order_id": o.id,
            "client": client_name,
            "date": formatted_date,
            "total": o.total_amount
        })

    # CÁLCULO DE TOP PRODUCTOS/COMBOS VENDIDOS
    items_summary = {}
    for d in details:
        name = "Item no especificado"
        if d.item_type == "PRODUCTO":
            p = db.query(Product).filter(Product.id == d.item_id).first()
            if p: name = p.name
        elif d.item_type == "COMBO":
            c = db.query(Combo).filter(Combo.id == d.item_id).first()
            if c: name = f"📦 {c.name}"

        items_summary[name] = items_summary.get(name, 0) + d.quantity

    # Ordenar y sacar el Top 5 de artículos de Charm Resin
    top_items = [{"name": k, "value": v} for k, v in
                 sorted(items_summary.items(), key=lambda x: x[1], reverse=True)[:5]]

    total_orders = len(orders)
    avg_ticket = (total_revenue / total_orders) if total_orders > 0 else 0.0

    return {
        "status": "success",
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "avg_ticket": round(avg_ticket, 2),
        "top_items": top_items,
        "history": history
    }