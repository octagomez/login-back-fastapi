from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, Session
from products import Product
from database import get_session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from models import User

from apis import get_current_user

router_products = APIRouter()

class ProductCreate(BaseModel):
    nombre: str
    email: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    empresa: Optional[str] = None

class ProductUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    empresa: Optional[str] = None
    activo: Optional[bool] = None

@router_products.get("/health")
def health_check(session: Session = Depends(get_session)):
    try:
        result = session.exec(select(Product).limit(1)).all()
        return {"status": "healthy", "message": "Base de datos funcionando correctamente", "tabla_Products": "existe"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Error en base de datos: {str(e)}", "tabla_Products": "no existe"}

@router_products.post("/products", response_model=Product)
def create_Product(Product: ProductCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    print(f"Datos recibidos: {Product}")
    existing_Product = session.exec(select(Product).where(Product.email == Product.email)).first()
    if existing_Product:
        raise HTTPException(status_code=400, detail="Ya existe un Product con ese email")
    try:
        db_Product = Product(
            nombre=Product.nombre,

            fecha_creacion=datetime.now().isoformat(),
            fecha_actualizacion=datetime.now().isoformat()
        )
        print(f"Product a crear: {db_Product}")
        session.add(db_Product)
        session.commit()
        session.refresh(db_Product)
        return db_Product
    except Exception as e:
        print(f"Error al crear Product: {e}")
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router_products.get("/products", response_model=List[Product])
def get_Products(skip: int = 0, limit: int = 100, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    Products = session.exec(select(Product).offset(skip).limit(limit)).all()
    return Products

@router_products.get("/products/{Product_id}", response_model=Product)
def get_Product(Product_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    Product = session.get(Product, Product_id)
    if not Product:
        raise HTTPException(status_code=404, detail="Product no encontrado")
    return Product

@router_products.put("/products/{Product_id}", response_model=Product)
def update_Product(Product_id: int, Product_update: ProductUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    Product = session.get(Product, Product_id)
    if not Product:
        raise HTTPException(status_code=404, detail="Product no encontrado")
    if Product_update.email and Product_update.email != Product.email:
        existing_Product = session.exec(select(Product).where(Product.email == Product_update.email)).first()
        if existing_Product:
            raise HTTPException(status_code=400, detail="Ya existe un Product con ese email")
    update_data = Product_update.dict(exclude_unset=True)
    update_data["fecha_actualizacion"] = datetime.now().isoformat()
    for field, value in update_data.items():
        setattr(Product, field, value)
    session.add(Product)
    session.commit()
    session.refresh(Product)
    return Product

@router_products.delete("/products/{Product_id}")
def delete_Product(Product_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    Product = session.get(Product, Product_id)
    if not Product:
        raise HTTPException(status_code=404, detail="Product no encontrado")
    session.delete(Product)
    session.commit()
    return {"message": "Product eliminado exitosamente"}

@router_products.get("/products/activos", response_model=List[Product])
def get_Products_activos(skip: int = 0, limit: int = 100, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    Products = session.exec(select(Product).where(Product.activo == True).offset(skip).limit(limit)).all()
    return Products

@router_products.post("/products/{Product_id}/activar")
def activar_Product(Product_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    Product = session.get(Product, Product_id)
    if not Product:
        raise HTTPException(status_code=404, detail="Product no encontrado")
    Product.activo = True
    Product.fecha_actualizacion = datetime.now().isoformat()
    session.add(Product)
    session.commit()
    return {"message": "Product activado exitosamente"}

@router_products.post("/products/{Product_id}/desactivar")
def desactivar_Product(Product_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    Product = session.get(Product, Product_id)
    if not Product:
        raise HTTPException(status_code=404, detail="Product no encontrado")
    Product.activo = False
    Product.fecha_actualizacion = datetime.now().isoformat()
    session.add(Product)
    session.commit()
    return {"message": "Product desactivado exitosamente"} 