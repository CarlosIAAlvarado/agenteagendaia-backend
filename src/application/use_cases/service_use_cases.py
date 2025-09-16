from typing import List, Optional, Dict, Any
from datetime import datetime
import csv
import json
import io
from ..dto.service_dto import ServiceDTO, ServiceCreateDTO, ServiceUpdateDTO
from ...domain.entities.service import Service, ServiceType, ServiceMode
from ...domain.repositories.service_repository import IServiceRepository
import logging

logger = logging.getLogger(__name__)


class ServiceUseCases:
    """Use cases for service management"""
    
    def __init__(self, service_repository: IServiceRepository):
        self._service_repo = service_repository
    
    async def get_all_services(self, skip: int = 0, limit: int = 100) -> List[ServiceDTO]:
        """Get all services with pagination"""
        try:
            services = await self._service_repo.get_all(skip=skip, limit=limit)
            return [self._service_to_dto(service) for service in services]
        except Exception as e:
            logger.error(f"Error in get_all_services use case: {e}")
            raise
    
    async def get_active_services(self, skip: int = 0, limit: int = 100) -> List[ServiceDTO]:
        """Get all active services"""
        try:
            services = await self._service_repo.get_active_services(skip=skip, limit=limit)
            return [self._service_to_dto(service) for service in services]
        except Exception as e:
            logger.error(f"Error in get_active_services use case: {e}")
            raise
    
    async def get_service_by_id(self, service_id: str) -> Optional[ServiceDTO]:
        """Get service by ID"""
        try:
            service = await self._service_repo.get_by_id(service_id)
            return self._service_to_dto(service) if service else None
        except Exception as e:
            logger.error(f"Error in get_service_by_id use case: {e}")
            raise
    
    async def search_services_by_name(self, name: str, skip: int = 0, limit: int = 50) -> List[ServiceDTO]:
        """Search services by name"""
        try:
            services = await self._service_repo.search_by_name(name, skip=skip, limit=limit)
            return [self._service_to_dto(service) for service in services]
        except Exception as e:
            logger.error(f"Error in search_services_by_name use case: {e}")
            raise
    
    async def get_services_by_type(self, service_type: str, skip: int = 0, limit: int = 50) -> List[ServiceDTO]:
        """Get services by type"""
        try:
            # Convert string to ServiceType enum
            try:
                service_type_enum = ServiceType(service_type.lower())
            except ValueError:
                raise ValueError(f"Invalid service type: {service_type}")
            
            services = await self._service_repo.get_by_type(service_type_enum, skip=skip, limit=limit)
            return [self._service_to_dto(service) for service in services]
        except Exception as e:
            logger.error(f"Error in get_services_by_type use case: {e}")
            raise
    
    async def create_service(self, service_data: ServiceCreateDTO) -> ServiceDTO:
        """Create a new service"""
        try:
            # Create service entity directly
            service = Service(
                id=None,
                name=service_data.name,
                description=service_data.description,
                duration_minutes=service_data.duration_minutes,
                service_type=ServiceType(service_data.service_type),
                service_mode=ServiceMode(service_data.service_mode),
                category_id=service_data.category_id,
                price=service_data.price,
                is_active=True,  # Default to active for new services
                created_at=datetime.utcnow()
            )
            
            # Save to repository
            created_service = await self._service_repo.create(service)
            return self._service_to_dto(created_service)
            
        except Exception as e:
            logger.error(f"Error in create_service use case: {e}")
            raise
    
    async def update_service(self, service_id: str, service_data: ServiceUpdateDTO) -> Optional[ServiceDTO]:
        """Update existing service"""
        try:
            # Get existing service
            service = await self._service_repo.get_by_id(service_id)
            if not service:
                return None
            
            # Update fields if provided
            if service_data.name is not None:
                service.update_service(name=service_data.name)
            
            if service_data.description is not None:
                service.update_service(description=service_data.description)
            
            if service_data.duration_minutes is not None:
                service.update_service(duration_minutes=service_data.duration_minutes)
            
            if service_data.price is not None:
                service.update_service(price=service_data.price)
            
            if service_data.service_type is not None:
                service.service_type = ServiceType(service_data.service_type)
            
            if service_data.service_mode is not None:
                service.service_mode = ServiceMode(service_data.service_mode)
            
            if service_data.is_active is not None:
                if service_data.is_active:
                    service.activate()
                else:
                    service.deactivate()
            
            # Save updated service
            updated_service = await self._service_repo.update(service)
            return self._service_to_dto(updated_service)
            
        except Exception as e:
            logger.error(f"Error in update_service use case: {e}")
            raise
    
    async def delete_service(self, service_id: str) -> bool:
        """Delete service by ID"""
        try:
            return await self._service_repo.delete(service_id)
        except Exception as e:
            logger.error(f"Error in delete_service use case: {e}")
            raise
    
    async def activate_service(self, service_id: str) -> Optional[ServiceDTO]:
        """Activate service"""
        try:
            service = await self._service_repo.get_by_id(service_id)
            if not service:
                return None
            
            service.activate()
            updated_service = await self._service_repo.update(service)
            return self._service_to_dto(updated_service)
            
        except Exception as e:
            logger.error(f"Error in activate_service use case: {e}")
            raise
    
    async def deactivate_service(self, service_id: str) -> Optional[ServiceDTO]:
        """Deactivate service"""
        try:
            service = await self._service_repo.get_by_id(service_id)
            if not service:
                return None
            
            service.deactivate()
            updated_service = await self._service_repo.update(service)
            return self._service_to_dto(updated_service)
            
        except Exception as e:
            logger.error(f"Error in deactivate_service use case: {e}")
            raise
    
    async def get_services_stats(self) -> Dict[str, Any]:
        """Get services statistics summary"""
        try:
            total_services = await self._service_repo.count_total()
            active_services = await self._service_repo.count_active()
            
            # Get services by type counts
            type_counts = {}
            for service_type in ServiceType:
                count = await self._service_repo.count_by_type(service_type)
                type_counts[service_type.value] = count
            
            return {
                "total_services": total_services,
                "active_services": active_services,
                "inactive_services": total_services - active_services,
                "services_by_type": type_counts,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in get_services_stats use case: {e}")
            raise
    
    def _service_to_dto(self, service: Service) -> ServiceDTO:
        """Convert Service entity to ServiceDTO"""
        return ServiceDTO(
            id=service.id,
            name=service.name,
            description=service.description,
            duration_minutes=service.duration_minutes,
            service_type=service.service_type.value,
            service_mode=service.service_mode.value,
            category_id=service.category_id,
            category_name=None,  # Will be populated by repository if needed
            price=service.price,
            is_active=service.is_active,
            created_at=service.created_at.isoformat() if service.created_at else None,
            updated_at=service.updated_at.isoformat() if service.updated_at else None
        )
    
    async def bulk_upload_services(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process bulk upload of services from CSV or JSON file"""
        try:
            successful_uploads = []
            failed_uploads = []
            errors = []
            
            # Decode file content
            content_str = file_content.decode('utf-8')
            
            # Parse based on file type
            if filename.endswith('.csv'):
                services_data = self._parse_csv_content(content_str)
            elif filename.endswith('.json'):
                services_data = self._parse_json_content(content_str)
            else:
                raise ValueError("Unsupported file format")
            
            # Process each service
            for i, service_data in enumerate(services_data, 1):
                try:
                    # Validate and create service DTO
                    service_dto = ServiceCreateDTO(**service_data)
                    
                    # Create service
                    created_service = await self.create_service(service_dto)
                    successful_uploads.append({
                        'row': i,
                        'name': created_service.name,
                        'id': created_service.id
                    })
                    
                except Exception as e:
                    error_msg = f"Row {i}: {str(e)}"
                    failed_uploads.append({
                        'row': i,
                        'data': service_data,
                        'error': str(e)
                    })
                    errors.append(error_msg)
                    logger.error(f"Bulk upload error at row {i}: {e}")
            
            return {
                'total_processed': len(services_data),
                'successful_uploads': len(successful_uploads),
                'failed_uploads': len(failed_uploads),
                'success_details': successful_uploads,
                'failed_details': failed_uploads,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error in bulk_upload_services use case: {e}")
            raise
    
    def _parse_csv_content(self, content: str) -> List[Dict[str, Any]]:
        """Parse CSV content and return list of service dictionaries"""
        try:
            csv_reader = csv.DictReader(io.StringIO(content))
            services = []
            
            for row in csv_reader:
                # Clean and validate data
                service_data = {
                    'name': row.get('name', '').strip(),
                    'description': row.get('description', '').strip(),
                    'duration_minutes': int(row.get('duration_minutes', 0)),
                    'service_type': row.get('service_type', '').strip().lower(),
                    'service_mode': row.get('service_mode', '').strip().lower(),
                    'category_id': row.get('category_id', '').strip() or None,
                    'price': float(row.get('price', 0)) if row.get('price') else None
                }
                
                # Validate service_type
                if service_data['service_type'] not in ['medical', 'beauty', 'consultation', 'maintenance', 'other']:
                    service_data['service_type'] = 'other'
                
                # Validate service_mode
                if service_data['service_mode'] not in ['presential', 'virtual', 'both']:
                    service_data['service_mode'] = 'presential'
                
                services.append(service_data)
            
            return services
            
        except Exception as e:
            raise ValueError(f"Error parsing CSV content: {str(e)}")
    
    def _parse_json_content(self, content: str) -> List[Dict[str, Any]]:
        """Parse JSON content and return list of service dictionaries"""
        try:
            data = json.loads(content)
            
            # Handle both array of objects and object with services array
            if isinstance(data, list):
                services_data = data
            elif isinstance(data, dict) and 'services' in data:
                services_data = data['services']
            else:
                raise ValueError("JSON must be an array of services or object with 'services' array")
            
            services = []
            for service_data in services_data:
                # Clean and validate data
                clean_data = {
                    'name': str(service_data.get('name', '')).strip(),
                    'description': str(service_data.get('description', '')).strip(),
                    'duration_minutes': int(service_data.get('duration_minutes', 0)),
                    'service_type': str(service_data.get('service_type', '')).strip().lower(),
                    'service_mode': str(service_data.get('service_mode', '')).strip().lower(),
                    'category_id': str(service_data.get('category_id', '')).strip() or None,
                    'price': float(service_data.get('price', 0)) if service_data.get('price') else None
                }
                
                # Validate service_type
                if clean_data['service_type'] not in ['medical', 'beauty', 'consultation', 'maintenance', 'other']:
                    clean_data['service_type'] = 'other'
                
                # Validate service_mode
                if clean_data['service_mode'] not in ['presential', 'virtual', 'both']:
                    clean_data['service_mode'] = 'presential'
                
                services.append(clean_data)
            
            return services
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing JSON content: {str(e)}")