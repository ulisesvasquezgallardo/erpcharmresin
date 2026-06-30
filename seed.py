import logging
from database import SessionLocal, engine, Base
from models.models import Product, Combo, ComboComponent
import models.models

# Configuración del registrador de auditoría
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ERP_CHARM_RESIN_SEED")


def seed_data():
    db = SessionLocal()
    try:
        # 1. LIMPIEZA ABSOLUTA DEL INVENTARIO ACTUAL (Cascada Manual Controlada)
        logger.info("🗑️ Iniciando purga completa del inventario anterior...")
        db.query(ComboComponent).delete()
        db.query(Combo).delete()
        db.query(Product).delete()
        db.commit()
        logger.info("✅ Base de datos limpia y lista para el catálogo de Charm Resin.")

        logger.info("🌱 Inyectando catálogo completo de Charm Resin (Edición 2026-2027)...")

        # LISTA MAESTRA DE PRODUCTOS POR PRESENTACIONES (Precios S/. y Stocks de Simulación)
        raw_products = [
            # === LÍNEA CREATIVE ===
            # Resina Epóxica Superclear 1:1 Premium
            {"sku": "CR-SUP-1KG", "name": "Resina Epóxica Superclear 1:1 Premium (1 KG)", "stock": 120,
             "unit_price": 75.00},
            {"sku": "CR-SUP-1GL", "name": "Resina Epóxica Superclear 1:1 Premium (1 GL)", "stock": 50,
             "unit_price": 240.00},
            {"sku": "CR-SUP-8KG", "name": "Resina Epóxica Superclear 1:1 Premium (8 KG)", "stock": 25,
             "unit_price": 460.00},
            {"sku": "CR-SUP-16KG", "name": "Resina Epóxica Superclear 1:1 Premium (16 KG)", "stock": 15,
             "unit_price": 850.00},
            {"sku": "CR-SUP-20KG", "name": "Resina Epóxica Superclear 1:1 Premium (20 KG)", "stock": 12,
             "unit_price": 1020.00},

            # Pigmento Translúcido Líquido (Gama de Colores Múltiples)
            {"sku": "CR-PIG-TRA-15ML", "name": "Pigmento Translúcido Concentrado (15 ML)", "stock": 200,
             "unit_price": 15.00},
            {"sku": "CR-PIG-TRA-1LT", "name": "Pigmento Translúcido Concentrado (1 LT)", "stock": 30,
             "unit_price": 180.00},

            # Resina UV Premium Fotocurable
            {"sku": "CR-UV-200ML", "name": "Resina UV Premium Hard Type (200 ML)", "stock": 90, "unit_price": 45.00},
            {"sku": "CR-UV-1LT", "name": "Resina UV Premium Hard Type (1 LT)", "stock": 20, "unit_price": 195.00},

            # Resina Epóxica Deep Pour Estructural 3:1 (Mesas River de Gran Espesor)
            {"sku": "CR-DEEP-1GL", "name": "Resina Deep Pour Estructural 3:1 (1 GL)", "stock": 40,
             "unit_price": 260.00},
            {"sku": "CR-DEEP-20KG", "name": "Resina Deep Pour Estructural 3:1 (20 KG)", "stock": 15,
             "unit_price": 1150.00},
            {"sku": "CR-DEEP-60KG", "name": "Resina Deep Pour Estructural 3:1 (60 KG)", "stock": 8,
             "unit_price": 3200.00},
            {"sku": "CR-DEEP-90KG", "name": "Resina Deep Pour Estructural 3:1 (90 KG)", "stock": 5,
             "unit_price": 4650.00},

            # Resina Flexible 3:1 (Efecto Domo / Stickers)
            {"sku": "CR-FLEX-1GL", "name": "Resina Flexible 3:1 Efecto Domo (1 GL)", "stock": 35, "unit_price": 250.00},
            {"sku": "CR-FLEX-20KG", "name": "Resina Flexible 3:1 Efecto Domo (20 KG)", "stock": 10,
             "unit_price": 1100.00},
            {"sku": "CR-FLEX-60KG", "name": "Resina Flexible 3:1 Efecto Domo (60 KG)", "stock": 6,
             "unit_price": 3100.00},
            {"sku": "CR-FLEX-90KG", "name": "Resina Flexible 3:1 Efecto Domo (90 KG)", "stock": 4,
             "unit_price": 4400.00},

            # === LÍNEA ARCHITECTURAL / INDUSTRIAL ===
            # Resina Porcelanato Líquido / Pisos Metálicos 3D
            {"sku": "AR-PORC-1KG", "name": "Resina Porcelanato Líquido / 3D (1 KG)", "stock": 80, "unit_price": 80.00},
            {"sku": "AR-PORC-1GL", "name": "Resina Porcelanato Líquido / 3D (1 GL)", "stock": 60, "unit_price": 265.00},
            {"sku": "AR-PORC-20KG", "name": "Resina Porcelanato Líquido / 3D (20 KG)", "stock": 20,
             "unit_price": 1180.00},
            {"sku": "AR-PORC-60KG", "name": "Resina Porcelanato Líquido / 3D (60 KG)", "stock": 10,
             "unit_price": 3350.00},
            {"sku": "AR-PORC-90KG", "name": "Resina Porcelanato Líquido / 3D (90 KG)", "stock": 6,
             "unit_price": 4800.00},

            # Pigmentos Especializados para Pisos (Metálicos en Polvo y Pasta Mármol)
            {"sku": "AR-PIG-MET-30G", "name": "Pigmento Metálico en Polvo 3D Flow (30 GR)", "stock": 150,
             "unit_price": 18.00},
            {"sku": "AR-PIG-MET-1KG", "name": "Pigmento Metálico en Polvo 3D Flow (1 KG)", "stock": 25,
             "unit_price": 190.00},
            {"sku": "AR-PIG-MET-5KG", "name": "Pigmento Metálico en Polvo 3D Flow (5 KG)", "stock": 10,
             "unit_price": 800.00},
            {"sku": "AR-PIG-PAS-30G", "name": "Pigmento en Pasta para Mármol Líquido (30 GR)", "stock": 140,
             "unit_price": 15.00},
            {"sku": "AR-PIG-PAS-250G", "name": "Pigmento en Pasta para Mármol Líquido (250 GR)", "stock": 45,
             "unit_price": 65.00},
            {"sku": "AR-PIG-PAS-1KG", "name": "Pigmento en Pasta para Mármol Líquido (1 KG)", "stock": 20,
             "unit_price": 195.00},
            {"sku": "AR-PIG-PAS-5KG", "name": "Pigmento en Pasta para Mármol Líquido (5 KG)", "stock": 8,
             "unit_price": 850.00},

            # Chips / Escamas Decorativas
            {"sku": "AR-CHIP-05KG", "name": "Chips Decorativos para Garajes / Pisos (½ KG)", "stock": 100,
             "unit_price": 25.00},
            {"sku": "AR-CHIP-1KG", "name": "Chips Decorativos para Garajes / Pisos (1 KG)", "stock": 70,
             "unit_price": 45.00},

            # Imprimantes, Primers y Pinturas de Base
            {"sku": "AR-PINT-BASE-1GL", "name": "Pintura Base Epóxica Acabado Uniforme (1 GL)", "stock": 40,
             "unit_price": 145.00},
            {"sku": "AR-PINT-BASE-20L", "name": "Pintura Base Epóxica Acabado Uniforme (20 LT)", "stock": 15,
             "unit_price": 660.00},
            {"sku": "AR-PRIM-ACR-1GL", "name": "Primer Acrílico Regulador de Absorción (1 GL)", "stock": 50,
             "unit_price": 55.00},
            {"sku": "AR-PRIM-ACR-20L", "name": "Primer Acrílico Regulador de Absorción (20 LT)", "stock": 18,
             "unit_price": 240.00},
            {"sku": "AR-PRIM-EPO-1GL", "name": "Primer Epóxico de Alta Penetración 3:1 (1 GL)", "stock": 45,
             "unit_price": 165.00},
            {"sku": "AR-PRIM-EPO-20K", "name": "Primer Epóxico de Alta Penetración 3:1 (20 KG)", "stock": 14,
             "unit_price": 750.00},

            # Preparación de Superficies, Polvos Cementicios y Reparación
            {"sku": "AR-AUTO-CEM-25K", "name": "Autonivelante Cementicio Industrial (Bolsa 25 KG)", "stock": 100,
             "unit_price": 65.00},
            {"sku": "AR-BASE-NIV-25K", "name": "Base Niveladora de Imperfecciones (Bolsa 25 KG)", "stock": 80,
             "unit_price": 52.00},
            {"sku": "AR-MASI-EPO-1KG", "name": "Masilla Epóxica 100% Sólidos 1:1 (1 KG)", "stock": 60,
             "unit_price": 55.00},
            {"sku": "AR-MASI-EPO-1GL", "name": "Masilla Epóxica 100% Sólidos 1:1 (1 GL)", "stock": 20,
             "unit_price": 195.00},
            {"sku": "AR-ALC-ISOP-1LT", "name": "Alcohol Isopropílico Desburbujador / Limpieza (1 LT)", "stock": 120,
             "unit_price": 22.00},
            {"sku": "AR-ALC-ISOP-1GL", "name": "Alcohol Isopropílico Desburbujador / Limpieza (1 GL)", "stock": 40,
             "unit_price": 75.00},

            # Sistemas de Impermeabilización Avanzada y Revestimientos
            {"sku": "AR-LLUVIA-1GL", "name": "Lluvia Acero Impermeabilizante Elastomérico (1 GL)", "stock": 30,
             "unit_price": 85.00},
            {"sku": "AR-LLUVIA-5GL", "name": "Lluvia Acero Impermeabilizante Elastomérico (5 GL)", "stock": 15,
             "unit_price": 380.00},
            {"sku": "AR-MICRO-SET5K", "name": "Microcemento Continuo Industrial (Kit 5 KG)", "stock": 25,
             "unit_price": 130.00},
            {"sku": "AR-MICRO-SET20", "name": "Microcemento Continuo Industrial (Kit 20 KG)", "stock": 12,
             "unit_price": 440.00},
            {"sku": "AR-ULTRA-SELL-1G", "name": "Ultra Sellador Polimérico Microcemento (1 GL)", "stock": 35,
             "unit_price": 95.00},
            {"sku": "AR-ULTRA-SELL-20L", "name": "Ultra Sellador Polimérico Microcemento (20 LT)", "stock": 10,
             "unit_price": 420.00},

            # Sistemas Industriales Pesados de Alto Reticulado y Capas Finales
            {"sku": "IN-RES-21-1GL", "name": "Resina 2:1 Pisos Industriales 100% Sólidos (1 GL)", "stock": 30,
             "unit_price": 275.00},
            {"sku": "IN-RES-21-20KG", "name": "Resina 2:1 Pisos Industriales 100% Sólidos (20 KG)", "stock": 15,
             "unit_price": 1220.00},
            {"sku": "IN-RES-21-60KG", "name": "Resina 2:1 Pisos Industriales 100% Sólidos (60 KG)", "stock": 8,
             "unit_price": 3450.00},
            {"sku": "IN-RES-21-90KG", "name": "Resina 2:1 Pisos Industriales 100% Sólidos (90 KG)", "stock": 4,
             "unit_price": 4950.00},
            {"sku": "IN-URET-PRO-1GL", "name": "Uretano Pro Capa Final Anti-rayado (1 GL)", "stock": 40,
             "unit_price": 185.00},
            {"sku": "IN-URET-PRO-20L", "name": "Uretano Pro Capa Final Anti-rayado (20 LT)", "stock": 12,
             "unit_price": 840.00},
            {"sku": "IN-ESM-ALT-1GL", "name": "Esmalte Epóxico Industrial Poliamida (1 GL)", "stock": 50,
             "unit_price": 155.00},
            {"sku": "IN-ESM-ALT-20KG", "name": "Esmalte Epóxico Industrial Poliamida (20 KG)", "stock": 18,
             "unit_price": 710.00},
            {"sku": "IN-ESM-ALT-60KG", "name": "Esmalte Epóxico Industrial Poliamida (60 KG)", "stock": 6,
             "unit_price": 1990.00},
            {"sku": "IN-POL-ALIF-1GL", "name": "Sellador Poliuretano Alifático Bicomponente (1 GL)", "stock": 30,
             "unit_price": 195.00},
            {"sku": "IN-POL-ALIF-20K", "name": "Sellador Poliuretano Alifático Bicomponente (20 KG)", "stock": 10,
             "unit_price": 890.00},

            # Morteros de Ultra-Resistencia y Especialidades Industriales
            {"sku": "IN-CHARMFLEX-20K", "name": "Charmflex Mortero de Compresión 16,000 psi (20 KG)", "stock": 15,
             "unit_price": 950.00},
            {"sku": "IN-CHARMFLEX-60K", "name": "Charmflex Mortero de Compresión 16,000 psi (60 KG)", "stock": 5,
             "unit_price": 2750.00},
            {"sku": "IN-MORT-AUTO-25K", "name": "Mortero Epóxico Autonivelante Industrial (Set 25 KG)", "stock": 20,
             "unit_price": 390.00},
            {"sku": "IN-CHARMCRETE-30K", "name": "Charmcrete Autonivelante Poliuretano Cementicio (30 KG)", "stock": 12,
             "unit_price": 1480.00},
            {"sku": "IN-LOSAS-DEPO-1G", "name": "Pintura Elastomérica para Losas Deportivas (1 GL)", "stock": 35,
             "unit_price": 85.00},
            {"sku": "IN-LOSAS-DEPO-5G", "name": "Pintura Elastomérica para Losas Deportivas (5 GL)", "stock": 15,
             "unit_price": 390.00},
            {"sku": "IN-OXITRON-1GL", "name": "Oxitron Esmalte Anticorrosivo Metales (1 GL)", "stock": 45,
             "unit_price": 98.00},
        ]

        # Inyectar los productos base y mapear sus instancias creadas para los combos
        product_instances = {}
        for item in raw_products:
            p = Product(
                sku=item["sku"],
                name=item["name"],
                stock=item["stock"],
                unit_price=item["unit_price"]
            )
            db.add(p)
            product_instances[item["sku"]] = p

        db.flush()  # Conservamos los IDs autogenerados en memoria transaccional

        # 3. GENERACIÓN DE COMBOS DE NEGOCIO PARA LA SIMULACIÓN ERP
        logger.info("📦 Ensamblando Combos Comerciales empaquetados...")

        # Combo 1: Paquete Porcelanato Líquido Mármol Premium
        # Nota: Retiramos unit_price para ajustarnos estrictamente a tu modelo Combo actual
        combo_marmol = Combo(
            sku="CB-MARMOL-PREM",
            name="Combo Porcelanato Líquido Mármol Profesional (10-12 m²)"
        )
        db.add(combo_marmol)
        db.flush()

        # Componentes del Combo Mármol
        db.add_all([
            ComboComponent(combo_id=combo_marmol.id, product_id=product_instances["AR-PORC-1GL"].id, quantity=1),
            ComboComponent(combo_id=combo_marmol.id, product_id=product_instances["AR-PRIM-EPO-1GL"].id, quantity=1),
            ComboComponent(combo_id=combo_marmol.id, product_id=product_instances["AR-PIG-PAS-250G"].id, quantity=1)
        ])

        # Combo 2: Kit Creative Pro Bisutería Completo
        combo_creative = Combo(
            sku="CB-CREATIVE-ART",
            name="Combo Resina Artística Creative Pro + Filtro UV"
        )
        db.add(combo_creative)
        db.flush()

        # Componentes del Combo Creative
        db.add_all([
            ComboComponent(combo_id=combo_creative.id, product_id=product_instances["CR-SUP-1KG"].id, quantity=1),
            ComboComponent(combo_id=combo_creative.id, product_id=product_instances["CR-PIG-TRA-15ML"].id, quantity=1),
            ComboComponent(combo_id=combo_creative.id, product_id=product_instances["CR-UV-200ML"].id, quantity=1)
        ])

        # Confirmación ACID final en base de datos física
        db.commit()
        logger.info(
            f"🎉 ¡Éxito Absoluto! Se han registrado {len(raw_products)} productos con todas sus presentaciones y 2 combos empaquetados respetando tu modelo actual en erp_epoxicas.db.")

    except Exception as e:
        db.rollback()
        logger.critical(f"💥 Error fatal al poblar el nuevo catálogo de Charm Resin: {str(e)}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("🛠️ Forzando el despliegue del esquema físico e inyección de datos Charm Resin...")
    Base.metadata.create_all(bind=engine)
    seed_data()