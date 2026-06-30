from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.models import Client, Product, Combo, Order, OrderDetail, ItemType, DeliveryType
from schemas.schemas import OrderCreateSchema


def process_order(db: Session, order_data: OrderCreateSchema):
    try:
        # 1. Gestionar Cliente
        client = db.query(Client).filter(Client.document_number == order_data.client.document_number).first()
        if not client:
            client = Client(**order_data.client.model_dump())
            db.add(client)
            db.flush()  # Obtenemos el ID del cliente sin hacer commit

        # 2. Crear cabecera de la Orden
        new_order = Order(
            client_id=client.id,
            delivery_type=order_data.delivery_type,
            # Limpiamos los textos basura si es RECOJO, la BD acepta nulos
            district=order_data.district if order_data.delivery_type == DeliveryType.ENTREGA else None,
            address=order_data.address if order_data.delivery_type == DeliveryType.ENTREGA else None,
            est_delivery_date=order_data.est_delivery_date,
            total_amount=0.0  # Inicializamos la variable financiera
        )
        db.add(new_order)
        db.flush()

        total_order_amount = 0.0

        # 3. Procesar Items y Descontar Inventario (ACID: Todo o Nada)
        for item in order_data.items:
            unit_price = 0.0

            if item.item_type == ItemType.PRODUCTO:
                # BLINDAJE: with_for_update() evita que 2 vendedores vendan el mismo stock al mismo tiempo
                product = db.query(Product).with_for_update().filter(Product.id == item.item_id).first()
                if not product:
                    raise ValueError(f"Producto ID {item.item_id} no encontrado.")
                if product.stock < item.quantity:
                    raise ValueError(
                        f"Stock insuficiente para el SKU: {product.sku}. Solicitado: {item.quantity}, Disponible: {product.stock}")

                product.stock -= item.quantity
                unit_price = product.unit_price

            elif item.item_type == ItemType.COMBO:
                combo = db.query(Combo).filter(Combo.id == item.item_id).first()
                if not combo:
                    raise ValueError(f"Combo ID {item.item_id} no encontrado.")

                # Descontar stock de los componentes básicos del combo
                for component in combo.components:
                    req_qty = component.quantity * item.quantity
                    # Aplicamos el bloqueo también en los componentes del combo
                    product = db.query(Product).with_for_update().filter(Product.id == component.product_id).first()

                    if product.stock < req_qty:
                        raise ValueError(
                            f"Stock insuficiente de componente {product.sku} para armar el Combo {combo.sku}. Faltan: {req_qty - product.stock}")

                    product.stock -= req_qty

                    # El precio del combo es la suma del costo de sus componentes base
                    unit_price += (product.unit_price * component.quantity)

            # Acumulamos el subtotal de la línea
            line_total = unit_price * item.quantity
            total_order_amount += line_total

            # Guardamos el detalle CON el precio unitario congelado
            detail = OrderDetail(
                order_id=new_order.id,
                item_type=item.item_type,
                item_id=item.item_id,
                quantity=item.quantity,
                unit_price=unit_price
            )
            db.add(detail)

        # 4. Consolidar la parte financiera en la Orden
        new_order.total_amount = total_order_amount

        # Si llegamos aquí sin errores, la transacción es 100% segura
        db.commit()
        return {
            "status": "success",
            "order_id": new_order.id,
            "total_amount": total_order_amount,
            "message": "Orden procesada exitosamente."
        }

    except ValueError as e:
        db.rollback()  # Rollback íntegro si falla la regla de negocio
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")