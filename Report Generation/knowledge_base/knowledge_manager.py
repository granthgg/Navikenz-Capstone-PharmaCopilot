import os
import json
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import logging

# Disable chromadb telemetry to prevent posthog errors
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY'] = 'False'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger('chromadb.telemetry').setLevel(logging.CRITICAL)

class KnowledgeBaseManager:
    def __init__(self, base_path: str = "Report Generation/knowledge_base"):
        self.base_path = base_path
        self.vector_db_path = os.path.join(base_path, "embeddings", "vector_store")
        
        # Create necessary directories
        os.makedirs(self.vector_db_path, exist_ok=True)
        os.makedirs(os.path.join(base_path, "historical_data"), exist_ok=True)
        os.makedirs(os.path.join(base_path, "documentation"), exist_ok=True)
        os.makedirs(os.path.join(base_path, "templates"), exist_ok=True)
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Successfully loaded SentenceTransformer model")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.embedding_model = None
        
        # Initialize ChromaDB
        try:
            self.client = chromadb.PersistentClient(path=self.vector_db_path)
            logger.info("Successfully initialized ChromaDB client")
            
            # Create collections
            self.collections = {
                'historical_data': self.client.get_or_create_collection("historical_data"),
                'documentation': self.client.get_or_create_collection("documentation"),
                'templates': self.client.get_or_create_collection("templates")
            }
            logger.info("Successfully created/retrieved ChromaDB collections")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.client = None
            self.collections = {}
        
    def add_historical_data(self, data_type: str, data: Dict[str, Any]) -> bool:
        """Add historical data to vector database"""
        if not self.embedding_model or not self.client:
            logger.error("Embedding model or ChromaDB not available")
            return False
            
        try:
            # Convert data to text for embedding
            text_content = self._format_data_as_text(data)
            if not text_content:
                logger.warning("No text content generated from data")
                return False
                
            embedding = self.embedding_model.encode(text_content).tolist()
            
            # Generate unique ID
            doc_id = f"{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Add to collection
            self.collections['historical_data'].add(
                embeddings=[embedding],
                documents=[text_content],
                metadatas=[{
                    'type': data_type,
                    'timestamp': data.get('collection_timestamp', datetime.now().isoformat()),
                    'source': 'real_time_collection',
                    'data_size': len(str(data))
                }],
                ids=[doc_id]
            )
            
            logger.info(f"Successfully added historical data: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding historical data: {e}")
            return False
        
    def add_documentation(self, doc_type: str, content: str, metadata: Dict[str, Any]) -> bool:
        """Add documentation to vector database"""
        if not self.embedding_model or not self.client:
            logger.error("Embedding model or ChromaDB not available")
            return False
            
        try:
            embedding = self.embedding_model.encode(content).tolist()
            
            # Generate unique ID
            doc_id = f"{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            self.collections['documentation'].add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[{
                    'type': doc_type,
                    'timestamp': datetime.now().isoformat(),
                    **metadata
                }],
                ids=[doc_id]
            )
            
            logger.info(f"Successfully added documentation: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documentation: {e}")
            return False
        
    def search_relevant_context(self, query: str, collection: str = 'historical_data', 
                              n_results: int = 10) -> List[Dict[str, Any]]:
        """Search for relevant context using vector similarity"""
        if not self.embedding_model or not self.client or collection not in self.collections:
            logger.error(f"Cannot search: missing components or invalid collection '{collection}'")
            return []
            
        try:
            query_embedding = self.embedding_model.encode(query).tolist()
            
            results = self.collections[collection].query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            if not results['documents'] or not results['documents'][0]:
                logger.info(f"No results found for query in collection '{collection}'")
                return []
            
            context_results = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                context_results.append({
                    'content': doc,
                    'metadata': metadata,
                    'distance': distance,
                    'relevance_score': 1 - distance  # Convert distance to relevance score
                })
            
            # Sort by relevance (lower distance = higher relevance)
            context_results.sort(key=lambda x: x['distance'])
            
            logger.info(f"Found {len(context_results)} relevant results for query")
            return context_results
            
        except Exception as e:
            logger.error(f"Error searching for context: {e}")
            return []
        
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base collections"""
        stats = {}
        
        if not self.client:
            return {'error': 'ChromaDB not available'}
            
        try:
            for collection_name, collection in self.collections.items():
                try:
                    count = collection.count()
                    stats[collection_name] = {
                        'document_count': count,
                        'status': 'available'
                    }
                except Exception as e:
                    stats[collection_name] = {
                        'document_count': 0,
                        'status': f'error: {str(e)}'
                    }
                    
        except Exception as e:
            stats['error'] = f"Error getting collection stats: {str(e)}"
            
        return stats
        
    def get_recent_summary(self, data_type: str, hours: int = 24) -> Dict[str, Any]:
        """Get recent summary data for a specific data type"""
        if not self.client or 'historical_data' not in self.collections:
            return {'error': 'ChromaDB not available'}
            
        try:
            # Get all documents from historical_data collection
            results = self.collections['historical_data'].get()
            
            if not results['documents']:
                return {'status': 'no_data', 'message': f'No {data_type} data available'}
            
            # Filter by data type and time
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_data = []
            
            for i, (doc_id, metadata, document) in enumerate(zip(
                results['ids'], results['metadatas'], results['documents']
            )):
                if metadata.get('type') == data_type:
                    try:
                        doc_timestamp = datetime.fromisoformat(metadata.get('timestamp', ''))
                        if doc_timestamp >= cutoff_time:
                            recent_data.append({
                                'id': doc_id,
                                'content': document,
                                'metadata': metadata,
                                'timestamp': metadata.get('timestamp')
                            })
                    except (ValueError, TypeError):
                        # Skip documents with invalid timestamps
                        continue
            
            if not recent_data:
                return {'status': 'no_recent_data', 'message': f'No recent {data_type} data available'}
            
            # Analyze the data based on type
            if data_type == 'classification':
                return self._analyze_classification_data(recent_data)
            elif data_type == 'forecasting':
                return self._analyze_forecasting_data(recent_data)
            elif data_type == 'rl_actions':
                return self._analyze_rl_data(recent_data)
            else:
                return {
                    'status': 'success',
                    'total_records': len(recent_data),
                    'data_type': data_type,
                    'hours_analyzed': hours,
                    'message': f'Found {len(recent_data)} recent {data_type} records'
                }
                
        except Exception as e:
            logger.error(f"Error getting recent summary for {data_type}: {e}")
            return {'error': str(e)}
    
    def _analyze_classification_data(self, recent_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze recent classification data"""
        try:
            defect_probs = []
            quality_classes = []
            successful_predictions = 0
            
            for record in recent_data:
                content = record['content']
                # Extract defect probability from content
                if 'Defect probability:' in content:
                    try:
                        prob_str = content.split('Defect probability:')[1].split(',')[0].strip()
                        prob = float(prob_str)
                        defect_probs.append(prob)
                        successful_predictions += 1
                    except (ValueError, IndexError):
                        continue
                
                # Extract quality class from content
                if 'Quality class:' in content:
                    try:
                        class_str = content.split('Quality class:')[1].split(',')[0].strip()
                        quality_classes.append(class_str)
                    except IndexError:
                        continue
            
            if not defect_probs:
                return {'status': 'no_valid_data', 'message': 'No valid classification data found'}
            
            return {
                'status': 'success',
                'total_predictions': len(recent_data),
                'successful_predictions': successful_predictions,
                'average_defect_probability': sum(defect_probs) / len(defect_probs),
                'maximum_defect_probability': max(defect_probs),
                'minimum_defect_probability': min(defect_probs),
                'most_common_quality_class': max(set(quality_classes), key=quality_classes.count) if quality_classes else 'Unknown',
                'data_quality': 'good' if successful_predictions > 5 else 'limited'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing classification data: {e}")
            return {'error': str(e)}
    
    def _analyze_forecasting_data(self, recent_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze recent forecasting data"""
        try:
            horizons = []
            successful_forecasts = 0
            
            for record in recent_data:
                content = record['content']
                if 'Forecast horizon:' in content:
                    try:
                        horizon_str = content.split('Forecast horizon:')[1].split('minutes')[0].strip()
                        horizon = int(horizon_str)
                        horizons.append(horizon)
                        successful_forecasts += 1
                    except (ValueError, IndexError):
                        continue
            
            if not horizons:
                return {'status': 'no_valid_data', 'message': 'No valid forecasting data found'}
            
            return {
                'status': 'success',
                'total_forecasts': len(recent_data),
                'successful_forecasts': successful_forecasts,
                'average_horizon': sum(horizons) / len(horizons),
                'data_quality': 'good' if successful_forecasts > 5 else 'limited'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing forecasting data: {e}")
            return {'error': str(e)}
    
    def _analyze_rl_data(self, recent_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze recent RL action data"""
        try:
            action_types = []
            successful_actions = 0
            
            for record in recent_data:
                content = record['content']
                if 'model actions:' in content:
                    try:
                        actions_part = content.split('model actions:')[1].split('|')[0].strip()
                        if actions_part:
                            action_types.append(actions_part)
                            successful_actions += 1
                    except IndexError:
                        continue
            
            if not action_types:
                return {'status': 'no_valid_data', 'message': 'No valid RL action data found'}
            
            return {
                'status': 'success',
                'total_actions': len(recent_data),
                'successful_actions': successful_actions,
                'action_types': list(set(action_types)),
                'data_quality': 'good' if successful_actions > 5 else 'limited'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing RL data: {e}")
            return {'error': str(e)}
        
    def _format_data_as_text(self, data: Dict[str, Any]) -> str:
        """Convert structured data to searchable text"""
        text_parts = []
        
        try:
            # Handle forecasting data
            if 'forecast_data' in data:
                text_parts.append(f"Forecast horizon: {data.get('forecast_horizon', 0)} minutes")
                forecast_data = data.get('forecast_data', [])
                if forecast_data:
                    # Process first few forecast points
                    for i, forecast in enumerate(forecast_data[:3]):  # First 3 points
                        if isinstance(forecast, dict):
                            sensors = forecast.get('sensors', {})
                            if sensors:
                                sensor_values = [f"{k}: {v}" for k, v in sensors.items() if isinstance(v, (int, float))]
                                text_parts.append(f"Forecast point {i+1}: {', '.join(sensor_values)}")
                                
            # Handle defect prediction data
            if 'defect_prediction' in data:
                defect = data['defect_prediction']
                if defect.get('api_status') == 'success':
                    prob = defect.get('defect_probability', 0)
                    risk = defect.get('risk_level', 'Unknown')
                    conf = defect.get('confidence', 0)
                    text_parts.append(f"Defect probability: {prob:.3f}, Risk level: {risk}, Confidence: {conf:.3f}")
                    
            # Handle quality prediction data
            if 'quality_prediction' in data:
                quality = data['quality_prediction']
                if quality.get('api_status') == 'success':
                    quality_class = quality.get('quality_class', 'Unknown')
                    conf = quality.get('confidence', 0)
                    text_parts.append(f"Quality class: {quality_class}, Confidence: {conf:.3f}")
                    
            # Handle RL action data
            for model_key in ['baseline_model', 'current_model', 'new_model']:
                if model_key in data:
                    rl_data = data[model_key]
                    if rl_data.get('api_status') == 'success':
                        actions = rl_data.get('recommended_actions', {})
                        model_type = rl_data.get('model_type', model_key.replace('_model', ''))
                        action_text = []
                        
                        for action_name, value in actions.items():
                            if isinstance(value, (int, float)):
                                action_text.append(f"{action_name}: {value}")
                                
                        if action_text:
                            text_parts.append(f"{model_type} model actions: {', '.join(action_text)}")
                            
            # Add timestamp information
            timestamp = data.get('collection_timestamp')
            if timestamp:
                text_parts.append(f"Collected at: {timestamp}")
                
            # Add API status information
            api_statuses = []
            for key, value in data.items():
                if isinstance(value, dict) and 'api_status' in value:
                    api_statuses.append(f"{key}: {value['api_status']}")
            if api_statuses:
                text_parts.append(f"API status: {', '.join(api_statuses)}")
                
        except Exception as e:
            logger.error(f"Error formatting data as text: {e}")
            # Fallback to basic string representation
            text_parts.append(f"Data: {str(data)[:500]}")  # First 500 chars
            
        result = " | ".join(text_parts)
        logger.debug(f"Formatted text length: {len(result)}")
        return result
        
    def cleanup_old_embeddings(self, days_to_keep: int = 30):
        """Clean up old embeddings from vector database"""
        if not self.client:
            logger.error("ChromaDB not available for cleanup")
            return
            
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_timestamp = cutoff_date.isoformat()
        
        try:
            for collection_name, collection in self.collections.items():
                # Get all documents with metadata
                results = collection.get()
                
                if results['metadatas']:
                    old_ids = []
                    for doc_id, metadata in zip(results['ids'], results['metadatas']):
                        doc_timestamp = metadata.get('timestamp', '')
                        if doc_timestamp < cutoff_timestamp:
                            old_ids.append(doc_id)
                    
                    if old_ids:
                        collection.delete(ids=old_ids)
                        logger.info(f"Cleaned up {len(old_ids)} old documents from {collection_name}")
                        
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            
    def initialize_default_documentation(self):
        """Initialize with comprehensive pharmaceutical documentation"""
        default_docs = [
            # Regulatory Guidelines
            {
                'type': 'regulatory_guideline',
                'content': '''21 CFR Part 11 Electronic Records and Electronic Signatures Guidelines:
                This regulation defines the criteria for electronic records and signatures to be considered trustworthy, 
                reliable, and equivalent to paper records. Key requirements include system validation, 
                audit trails, record integrity, user authentication, and controls for open systems. 
                Electronic records must be accurate, reliable, consistently maintained, and readily retrievable 
                throughout the record retention period. Systems must include operational controls, authority checks, 
                device checks, and determination that persons who develop, maintain, or use electronic records 
                have the education, training, and experience to perform their assigned tasks.''',
                'metadata': {'source': 'FDA', 'regulation': '21_CFR_11', 'priority': 'high'}
            },
            {
                'type': 'quality_standard',
                'content': '''Good Manufacturing Practice (GMP) Guidelines for Pharmaceutical Manufacturing:
                GMP ensures that products are consistently produced and controlled according to quality standards. 
                It covers all aspects of production from raw materials, premises and equipment to training and 
                personal hygiene of staff. Key requirements include: qualified personnel, adequate premises and equipment, 
                appropriate manufacturing procedures and controls, suitable storage and distribution, and adequate 
                laboratory controls. Quality control must include establishing, documenting, and following procedures 
                that will ensure the identity, strength, quality, and purity of drug products.''',
                'metadata': {'source': 'FDA', 'standard': 'GMP', 'priority': 'high'}
            },
            {
                'type': 'process_guideline',
                'content': '''Pharmaceutical Manufacturing Process Control:
                Critical process parameters include temperature control (±2°C tolerance), pressure monitoring 
                (±5% variance), flow rates (±3% accuracy), mixing speeds (RPM control ±1%), and compression forces 
                (±2% tolerance). These parameters must be continuously monitored and maintained within specified 
                ranges to ensure product quality. Process analytical technology (PAT) should be implemented for 
                real-time monitoring. Statistical process control (SPC) charts must be maintained for trend analysis.''',
                'metadata': {'source': 'internal', 'category': 'process_control', 'priority': 'high'}
            },
            # ICH Guidelines
            {
                'type': 'ich_guideline',
                'content': '''ICH Q7 Good Manufacturing Practice Guide for Active Pharmaceutical Ingredients:
                Quality risk management principles should be applied throughout the pharmaceutical quality system. 
                Risk assessments should be based on scientific knowledge and ultimately link to the protection of patients. 
                The level of effort, formality and documentation of the quality risk management process should be 
                commensurate with the level of risk. Quality risk management is a systematic process for the assessment, 
                control, communication and review of risks to the quality of the drug product across the product lifecycle.''',
                'metadata': {'source': 'ICH', 'standard': 'Q7', 'priority': 'high'}
            },
            # Quality Standards
            {
                'type': 'quality_standard',
                'content': '''Quality by Design (QbD) Principles:
                QbD is a systematic approach to pharmaceutical development that begins with predefined objectives 
                and emphasizes product and process understanding based on sound science and quality risk management. 
                Key elements include: Quality Target Product Profile (QTPP), Critical Quality Attributes (CQA), 
                Critical Process Parameters (CPP), Design Space, and Control Strategy. The design space is the 
                multidimensional combination of input variables and process parameters that provide assurance of quality.''',
                'metadata': {'source': 'FDA', 'standard': 'QbD', 'priority': 'medium'}
            },
            # Compliance Standards
            {
                'type': 'compliance_standard',
                'content': '''Data Integrity Guidelines (ALCOA+ Principles):
                Data must be Attributable, Legible, Contemporaneous, Original, and Accurate (ALCOA). The "+" 
                adds Complete, Consistent, Enduring, and Available. All data must be traceable to the individual 
                who performed the work and when it was performed. Records must be readable and permanent. 
                Data should be recorded at the time the work is performed. Original records must be preserved. 
                Data must be complete and include all required information.''',
                'metadata': {'source': 'FDA', 'standard': 'ALCOA_PLUS', 'priority': 'high'}
            },
            # Risk Management
            {
                'type': 'risk_management',
                'content': '''ICH Q9 Quality Risk Management:
                Risk management includes the systematic application of quality management policies, procedures, 
                and practices to the tasks of assessing, controlling, communicating and reviewing risk. 
                Risk assessment consists of risk identification, risk analysis, and risk evaluation. 
                Typical risk management tools include: Failure Mode Effects Analysis (FMEA), Fault Tree Analysis (FTA), 
                Hazard Analysis and Critical Control Points (HACCP), Hazard Operability Analysis (HAZOP), 
                Preliminary Hazard Analysis (PHA), and Risk Ranking and Filtering.''',
                'metadata': {'source': 'ICH', 'standard': 'Q9', 'priority': 'medium'}
            },
            # Process Validation
            {
                'type': 'validation_guideline',
                'content': '''Process Validation Guidelines:
                Process validation is defined as the collection and evaluation of data, from the process design stage 
                throughout commercial production, which establishes scientific evidence that a process is capable 
                of consistently delivering quality products. Process validation consists of three stages: 
                Stage 1 (Process Design), Stage 2 (Process Qualification), and Stage 3 (Continued Process Verification). 
                Critical Quality Attributes and Critical Process Parameters must be identified and monitored.''',
                'metadata': {'source': 'FDA', 'standard': 'Process_Validation', 'priority': 'high'}
            },
            # Analytical Standards
            {
                'type': 'analytical_standard',
                'content': '''Analytical Method Validation:
                Analytical procedures must be validated to demonstrate that they are suitable for their intended use. 
                Validation parameters include: Accuracy (bias), Precision (repeatability and reproducibility), 
                Specificity, Detection Limit, Quantitation Limit, Linearity, Range, and Robustness. 
                System suitability tests must be performed to verify that the analytical system is working properly. 
                Reference standards must be qualified and properly stored.''',
                'metadata': {'source': 'USP', 'standard': 'Analytical_Validation', 'priority': 'medium'}
            },
            # Environmental Monitoring
            {
                'type': 'environmental_standard',
                'content': '''Environmental Monitoring in Pharmaceutical Manufacturing:
                Environmental monitoring programs must be established for all classified areas. 
                Monitoring should include viable and non-viable particles, temperature, humidity, 
                and differential pressure. Action limits and alert limits must be established based on 
                historical data and risk assessment. Trending of environmental data is essential for 
                identifying potential issues before they impact product quality. Corrective and 
                Preventive Action (CAPA) systems must address environmental excursions.''',
                'metadata': {'source': 'internal', 'standard': 'Environmental_Monitoring', 'priority': 'medium'}
            },
            # Equipment Qualification
            {
                'type': 'equipment_standard',
                'content': '''Equipment Qualification and Validation:
                Equipment qualification consists of four phases: Design Qualification (DQ), Installation Qualification (IQ), 
                Operational Qualification (OQ), and Performance Qualification (PQ). DQ ensures equipment design is 
                suitable for intended use. IQ verifies correct installation. OQ demonstrates equipment operates 
                according to specifications across anticipated operating ranges. PQ demonstrates consistent 
                performance under normal operating conditions. Preventive maintenance programs must be established.''',
                'metadata': {'source': 'ISPE', 'standard': 'Equipment_Qualification', 'priority': 'medium'}
            }
        ]
        
        logger.info("Initializing comprehensive pharmaceutical documentation knowledge base")
        for doc in default_docs:
            success = self.add_documentation(doc['type'], doc['content'], doc['metadata'])
            if success:
                logger.info(f"Added {doc['type']}: {doc['metadata'].get('standard', doc['metadata'].get('regulation', 'unknown'))}")
        
        logger.info(f"Successfully initialized knowledge base with {len(default_docs)} pharmaceutical documents") 