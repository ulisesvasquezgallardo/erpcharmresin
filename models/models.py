from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Enum
from sqlalchemy.orm import relationship
import enum
from database import Base
import datetime


# --- ENUMERACIONES ---
class DocType(enum.Enum):
    DNI = "DNI"
    RUC = "RUC"


class DeliveryType(enum.Enum):
    ENTREGA = "ENTREGA"
    RECOJO = "RECOJO"


class ItemType(enum.Enum):
    PRODUCTO = "PRODUCTO"
    COMBO = "COMBO"


# --- MODELOS DE TABLAS ---
class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    doc_type = Column(Enum(DocType), nullable=False)
    document_number = Column(String(11), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)  # Nombre o Razón Social


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    stock = Column(Integer, default=0)
    unit_price = Column(Float, default=0.0)


class Combo(Base):
    __tablename__ = "combos"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)

    # MEJORA: cascade="all, delete-orphan" para limpiar la BD si se borra un combo
    components = relationship("ComboComponent", back_populates="combo", cascade="all, delete-orphan")


class ComboComponent(Base):
    __tablename__ = "combo_components"

    id = Column(Integer, primary_key=True, index=True)
    combo_id = Column(Integer, ForeignKey("combos.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)  # Cantidad del producto base necesaria

    combo = relationship("Combo", back_populates="components")
    product = relationship("Product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    order_datetime = Column(DateTime, default=datetime.datetime.utcnow)
    delivery_type = Column(Enum(DeliveryType), nullable=False)
    district = Column(String(50), nullable=True)  # Solo aplica si es ENTREGA
    address = Column(String(200), nullable=True)
    est_delivery_date = Column(Date, nullable=False)

    # Campo Financiero: Guarda el total recaudado en esta venta
    total_amount = Column(Float, default=0.0)

    # MEJORA: cascade="all, delete-orphan" para evitar detalles de facturas huérfanos
    details = relationship("OrderDetail", back_populates="order", cascade="all, delete-orphan")
    client = relationship("Client")


class OrderDetail(Base):
    __tablename__ = "order_details"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    item_type = Column(Enum(ItemType), nullable=False)
    item_id = Column(Integer, nullable=False)  # ID del Producto o Combo
    quantity = Column(Integer, nullable=False)

    # Campo Financiero: Congela el precio unitario al momento de la venta
    unit_price = Column(Float, nullable=False, default=0.0)

    order = relationship("Order", back_populates="details")


class InventoryLog(Base):
    __tablename__ = "inventory_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    product_sku = Column(String, index=True)
    old_stock = Column(Integer)
    new_stock = Column(Integer)
    reason = Column(String)