from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from datetime import date
from models.models import DocType, DeliveryType, ItemType


class ClientSchema(BaseModel):
    doc_type: DocType
    document_number: str = Field(..., description="Número de documento (DNI o RUC)")
    name: str = Field(..., description="Nombre o Razón Social")

    @model_validator(mode='after')
    def validate_document(self):
        doc = self.document_number
        if self.doc_type == DocType.DNI and (not doc.isdigit() or len(doc) != 8):
            raise ValueError("El DNI debe tener exactamente 8 dígitos numéricos.")
        if self.doc_type == DocType.RUC and (not doc.isdigit() or len(doc) != 11):
            raise ValueError("El RUC debe tener exactamente 11 dígitos numéricos.")
        return self


class OrderItemSchema(BaseModel):
    item_type: ItemType
    item_id: int = Field(..., gt=0, description="ID del Producto o Combo")
    quantity: int = Field(..., gt=0, description="La cantidad debe ser mayor a 0")


class OrderCreateSchema(BaseModel):
    client: ClientSchema
    delivery_type: DeliveryType
    district: Optional[str] = None
    address: Optional[str] = None
    est_delivery_date: date
    items: List[OrderItemSchema] = Field(..., min_length=1, description="El carrito no puede estar vacío")

    @model_validator(mode='after')
    def validate_delivery_details(self):
        # PROTECCIÓN: Si es ENTREGA, obligamos a que exista distrito y dirección
        if self.delivery_type == DeliveryType.ENTREGA:
            if not self.district or not self.address:
                raise ValueError("El distrito y la dirección son obligatorios para envíos a domicilio (ENTREGA).")

        # Si es RECOJO, podemos limpiar la dirección por si el vendedor escribió algo por error
        elif self.delivery_type == DeliveryType.RECOJO:
            self.district = None
            self.address = None

        return self


class StockUpdateSchema(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity_to_add: int = Field(..., gt=0)