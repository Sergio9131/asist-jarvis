"""
Módulo de base de datos simple (JSON)
Almacena información de clientes
"""

import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ClientDatabase:
    """Base de datos de clientes"""

    def __init__(self, db_path='clients.json'):
        # En Railway, usar directorio temporal
        if 'RAILWAY' in os.environ:
            db_path = '/tmp/clients.json'

        self.db_path = os.path.expanduser(db_path)
        self._ensure_db()

    def _ensure_db(self):
        """Crear DB si no existe"""
        if not os.path.exists(self.db_path):
            self._save({})

    def _load(self):
        """Cargar base de datos"""
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except:
            return {}

    def _save(self, data):
        """Guardar base de datos"""
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_client(self, phone):
        """Obtener cliente por teléfono"""
        db = self._load()
        return db.get(phone)

    def get_all_clients(self):
        """Obtener todos los clientes"""
        return self._load()

    def add_client(self, phone, name, notes=''):
        """Añadir nuevo cliente"""
        db = self._load()

        if phone in db:
            # Actualizar nombre si ya existe
            db[phone]['name'] = name
        else:
            db[phone] = {
                'name': name,
                'phone': phone,
                'notes': notes,
                'created_at': datetime.now().isoformat(),
                'last_contact': datetime.now().isoformat()
            }

        self._save(db)
        logger.info(f"Cliente añadido/actualizado: {phone}")

    def update_client(self, phone, data):
        """Actualizar cliente"""
        db = self._load()

        if phone in db:
            db[phone].update(data)
            db[phone]['last_contact'] = datetime.now().isoformat()
            self._save(db)
            return True

        return False

    def delete_client(self, phone):
        """Eliminar cliente"""
        db = self._load()

        if phone in db:
            del db[phone]
            self._save(db)
            return True

        return False
