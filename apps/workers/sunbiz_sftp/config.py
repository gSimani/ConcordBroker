"""
Configuration for Sunbiz SFTP Agent
"""

import os
from pathlib import Path
from typing import Dict, List

class Settings:
    """Configuration settings for Sunbiz SFTP data"""
    
    # SFTP Connection
    SFTP_HOST = "sftp.floridados.gov"
    SFTP_USERNAME = "Public"
    SFTP_PASSWORD = "PubAccess1845!"
    SFTP_PORT = 22
    
    # Database
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost/concordbroker'
    )
    
    # Data storage
    DATA_RAW_PATH = os.getenv('DATA_RAW_PATH', './data/raw')
    DATA_PROCESSED_PATH = os.getenv('DATA_PROCESSED_PATH', './data/processed')
    
    # File type definitions with field mappings
    FILE_DEFINITIONS = {
        'c': {
            'name': 'Corporate Filings',
            'delimiter': '|',
            'encoding': 'utf-8',
            'fields': [
                'doc_number', 'entity_name', 'entity_type', 'fei_number',
                'filing_date', 'status', 'principal_address', 'principal_city',
                'principal_state', 'principal_zip', 'mailing_address',
                'mailing_city', 'mailing_state', 'mailing_zip',
                'registered_agent_name', 'registered_agent_address',
                'registered_agent_city', 'registered_agent_state',
                'registered_agent_zip', 'officer1_name', 'officer1_title',
                'officer2_name', 'officer2_title', 'officer3_name', 'officer3_title'
            ]
        },
        'ce': {
            'name': 'Corporate Events',
            'delimiter': '|',
            'encoding': 'utf-8',
            'fields': [
                'doc_number', 'event_date', 'event_type', 'event_description',
                'filing_number', 'effective_date', 'document_code'
            ]
        },
        'fn': {
            'name': 'Fictitious Name Filings',
            'delimiter': '|',
            'encoding': 'utf-8',
            'fields': [
                'registration_number', 'name', 'owner_name', 'owner_type',
                'filing_date', 'expiration_date', 'status', 'county'
            ]
        },
        'fne': {
            'name': 'Fictitious Name Events',
            'delimiter': '|',
            'encoding': 'utf-8',
            'fields': [
                'registration_number', 'event_date', 'event_type',
                'event_description', 'filing_number'
            ]
        },
        'ft': {
            'name': 'Federal Tax Lien Filings',
            'delimiter': '|',
            'encoding': 'utf-8',
            'fields': [
                'lien_number', 'filing_date', 'lien_type', 'amount',
                'debtor_name', 'debtor_address', 'county'
            ]
        },
        'gp': {
            'name': 'General Partnership Filings',
            'delimiter': '|',
            'encoding': 'utf-8',
            'fields': [
                'registration_number', 'partnership_name', 'filing_date',
                'status', 'general_partner_name', 'general_partner_address',
                'county', 'business_address'
            ]
        },
        'mark': {
            'name': 'Trademark/Service Mark',
            'delimiter': '|',
            'encoding': 'utf-8',
            'fields': [
                'mark_id', 'mark_text', 'mark_type', 'owner_name',
                'filing_date', 'registration_date', 'expiration_date',
                'status', 'class_codes', 'description'
            ]
        }
    }
    
    # Entity type classifications
    ENTITY_TYPES = {
        'CORPORATION': ['CORP', 'INC', 'INCORPORATED'],
        'LLC': ['LLC', 'L.L.C.', 'LIMITED LIABILITY'],
        'PARTNERSHIP': ['LP', 'LLP', 'LLLP', 'PARTNERSHIP'],
        'NONPROFIT': ['NON-PROFIT', 'NONPROFIT', 'NOT FOR PROFIT'],
        'FOREIGN': ['FOREIGN', 'FOR PROFIT FOREIGN']
    }
    
    # Major registered agents to track
    MAJOR_REGISTERED_AGENTS = [
        'REGISTERED AGENT SOLUTIONS',
        'CORPORATION SERVICE COMPANY',
        'CT CORPORATION',
        'NORTHWEST REGISTERED AGENT',
        'LEGALZOOM',
        'INCFILE',
        'ROCKET LAWYER',
        'NATIONAL REGISTERED AGENTS',
        'COGENCY GLOBAL',
        'VCORP SERVICES'
    ]
    
    # Event type classifications
    EVENT_CLASSIFICATIONS = {
        'FORMATION': ['ARTICLES', 'INCORPORATION', 'ORGANIZATION', 'FORMATION'],
        'AMENDMENT': ['AMEND', 'AMENDMENT', 'RESTATED'],
        'DISSOLUTION': ['DISSOLV', 'DISSOLUTION', 'WITHDRAWAL', 'CANCEL'],
        'MERGER': ['MERGER', 'ACQUISITION', 'CONSOLIDATION'],
        'NAME_CHANGE': ['NAME CHANGE', 'DBA', 'FICTITIOUS'],
        'ANNUAL_REPORT': ['ANNUAL', 'REPORT', 'STATEMENT'],
        'REINSTATEMENT': ['REINSTATE', 'REVIVAL', 'RENEWAL']
    }
    
    # Alert thresholds
    ALERT_THRESHOLDS = {
        'daily_new_entities': 1000,  # Alert if more than 1000 new entities in a day
        'dissolution_surge': 100,    # Alert if more than 100 dissolutions
        'major_agent_growth': 50,    # Alert if agent adds 50+ entities in a day
        'foreign_entity_surge': 20   # Alert if 20+ foreign entities register
    }
    
    # Processing settings
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '1000'))
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '4'))
    RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '5'))
    
    # Download schedule (cron-like)
    DOWNLOAD_SCHEDULE = {
        'time': '03:00',  # 3 AM daily
        'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        'file_types': ['c', 'ce'],  # Corporate filings and events
        'retry_on_failure': True
    }
    
    def get_data_path(self, subdir: str = '') -> Path:
        """Get data directory path"""
        base_path = Path(self.DATA_RAW_PATH) / 'sunbiz_sftp'
        if subdir:
            base_path = base_path / subdir
        base_path.mkdir(parents=True, exist_ok=True)
        return base_path
    
    def get_file_definition(self, file_type: str) -> Dict:
        """Get file definition for a specific type"""
        return self.FILE_DEFINITIONS.get(file_type, {})
    
    def classify_entity_type(self, entity_type_str: str) -> str:
        """Classify entity type from string"""
        entity_type_upper = entity_type_str.upper() if entity_type_str else ''
        
        for category, keywords in self.ENTITY_TYPES.items():
            for keyword in keywords:
                if keyword in entity_type_upper:
                    return category
        
        return 'OTHER'
    
    def classify_event_type(self, event_type_str: str) -> str:
        """Classify event type from string"""
        event_type_upper = event_type_str.upper() if event_type_str else ''
        
        for category, keywords in self.EVENT_CLASSIFICATIONS.items():
            for keyword in keywords:
                if keyword in event_type_upper:
                    return category
        
        return 'OTHER'
    
    def is_major_agent(self, agent_name: str) -> bool:
        """Check if agent is a major registered agent"""
        if not agent_name:
            return False
        
        agent_upper = agent_name.upper()
        for major_agent in self.MAJOR_REGISTERED_AGENTS:
            if major_agent in agent_upper:
                return True
        
        return False

settings = Settings()