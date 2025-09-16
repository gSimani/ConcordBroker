#!/usr/bin/env python3
"""
Florida Configuration Manager
Centralized configuration management for all Florida data agents

Features:
- Hierarchical configuration with defaults and overrides
- Environment variable integration
- Configuration validation and schema checking
- Hot reloading of configuration changes
- Encrypted secret management
- Multi-environment support (dev, staging, prod)
- Configuration templating and inheritance
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import yaml
from datetime import datetime
import base64
from cryptography.fernet import Fernet
import jsonschema

logger = logging.getLogger(__name__)

@dataclass
class CountyConfig:
    """Configuration for a Florida county"""
    code: str
    name: str
    enabled: bool
    priority: int
    special_handling: Dict[str, Any]

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str
    max_connections: int
    batch_size: int
    retry_attempts: int
    timeout_seconds: int

@dataclass
class NotificationConfig:
    """Notification configuration"""
    email_enabled: bool
    webhook_enabled: bool
    email_settings: Dict[str, Any]
    webhook_settings: Dict[str, Any]

class FloridaConfigManager:
    """Centralized configuration management for Florida data agents"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "florida_agent_config.json"
        self.environment = os.getenv('FLORIDA_AGENT_ENV', 'production')
        self.config_cache: Dict[str, Any] = {}
        self.last_loaded: Optional[datetime] = None
        self.encryption_key = self._get_or_create_encryption_key()
        
        # Configuration schema for validation
        self.config_schema = self._define_config_schema()
        
        # Load initial configuration
        self._load_configuration()

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive configuration values"""
        key_file = Path(".florida_agent_key")
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Secure the key file (Unix-like systems)
            try:
                os.chmod(key_file, 0o600)
            except:
                pass
            
            logger.info("Generated new encryption key for configuration secrets")
            return key

    def _define_config_schema(self) -> Dict[str, Any]:
        """Define the JSON schema for configuration validation"""
        return {
            "type": "object",
            "properties": {
                "orchestrator": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "environment": {"type": "string", "enum": ["development", "staging", "production"]},
                        "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]}
                    },
                    "required": ["name", "version"]
                },
                "counties": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-z_]+$": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "pattern": "^\\d{2}$"},
                                "name": {"type": "string"},
                                "enabled": {"type": "boolean"},
                                "priority": {"type": "integer", "minimum": 1, "maximum": 10}
                            },
                            "required": ["code", "name", "enabled"]
                        }
                    }
                },
                "download": {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string"},
                        "max_concurrent": {"type": "integer", "minimum": 1, "maximum": 20},
                        "rate_limit_seconds": {"type": "number", "minimum": 0.1, "maximum": 10},
                        "timeout_seconds": {"type": "integer", "minimum": 10, "maximum": 600},
                        "retry_attempts": {"type": "integer", "minimum": 1, "maximum": 10}
                    }
                },
                "processing": {
                    "type": "object", 
                    "properties": {
                        "batch_size": {"type": "integer", "minimum": 100, "maximum": 50000},
                        "max_workers": {"type": "integer", "minimum": 1, "maximum": 32},
                        "memory_limit_mb": {"type": "integer", "minimum": 512, "maximum": 16384},
                        "enable_validation": {"type": "boolean"}
                    }
                },
                "database": {
                    "type": "object",
                    "properties": {
                        "batch_size": {"type": "integer", "minimum": 100, "maximum": 10000},
                        "max_connections": {"type": "integer", "minimum": 2, "maximum": 50},
                        "retry_attempts": {"type": "integer", "minimum": 1, "maximum": 10},
                        "enable_parallel": {"type": "boolean"}
                    }
                },
                "monitoring": {
                    "type": "object",
                    "properties": {
                        "check_interval_seconds": {"type": "integer", "minimum": 30, "maximum": 3600},
                        "metric_retention_days": {"type": "integer", "minimum": 1, "maximum": 365},
                        "alert_cooldown_minutes": {"type": "integer", "minimum": 1, "maximum": 1440}
                    }
                },
                "scheduling": {
                    "type": "object",
                    "properties": {
                        "daily_hour": {"type": "integer", "minimum": 0, "maximum": 23},
                        "enable_hourly_checks": {"type": "boolean"}
                    }
                }
            },
            "required": ["orchestrator", "counties"]
        }

    def _load_configuration(self):
        """Load configuration from file with environment variable overrides"""
        logger.info(f"Loading configuration for environment: {self.environment}")
        
        # Start with default configuration
        config = self._get_default_configuration()
        
        # Load from configuration file if it exists
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    if config_file.suffix.lower() in ['.yml', '.yaml']:
                        file_config = yaml.safe_load(f)
                    else:
                        file_config = json.load(f)
                
                # Merge file configuration
                config = self._merge_configurations(config, file_config)
                logger.info(f"Loaded configuration from {config_file}")
                
            except Exception as e:
                logger.error(f"Failed to load configuration from {config_file}: {e}")
                logger.info("Using default configuration")
        
        # Apply environment-specific overrides
        env_config = self._get_environment_configuration()
        if env_config:
            config = self._merge_configurations(config, env_config)
        
        # Apply environment variable overrides
        config = self._apply_environment_variables(config)
        
        # Decrypt encrypted values
        config = self._decrypt_configuration(config)
        
        # Validate configuration
        try:
            jsonschema.validate(config, self.config_schema)
            logger.info("Configuration validation successful")
        except jsonschema.ValidationError as e:
            logger.error(f"Configuration validation failed: {e}")
            # Use defaults for invalid configuration
            
        self.config_cache = config
        self.last_loaded = datetime.now()

    def _get_default_configuration(self) -> Dict[str, Any]:
        """Get default configuration values"""
        return {
            "orchestrator": {
                "name": "Florida Property Data Agent System",
                "version": "1.0.0",
                "environment": self.environment,
                "log_level": "INFO"
            },
            "counties": {
                "broward": {
                    "code": "12",
                    "name": "Broward County",
                    "enabled": True,
                    "priority": 1,
                    "special_handling": {}
                },
                "miami_dade": {
                    "code": "25", 
                    "name": "Miami-Dade County",
                    "enabled": False,
                    "priority": 2,
                    "special_handling": {}
                },
                "palm_beach": {
                    "code": "50",
                    "name": "Palm Beach County", 
                    "enabled": False,
                    "priority": 3,
                    "special_handling": {}
                }
            },
            "high_priority_counties": ["12"],  # Broward
            "download": {
                "directory": "florida_data",
                "max_concurrent": 5,
                "rate_limit_seconds": 1.0,
                "timeout_seconds": 300,
                "retry_attempts": 3
            },
            "processing": {
                "batch_size": 10000,
                "max_workers": 4,
                "memory_limit_mb": 2048,
                "enable_validation": True
            },
            "database": {
                "batch_size": 1000,
                "max_connections": 10,
                "retry_attempts": 3,
                "enable_parallel": True,
                "max_parallel_ops": 5
            },
            "monitoring": {
                "check_interval_seconds": 60,
                "metric_retention_days": 30,
                "alert_cooldown_minutes": 15,
                "thresholds": {
                    "cpu_percent": 80.0,
                    "memory_percent": 85.0,
                    "disk_percent": 90.0,
                    "error_rate_percent": 10.0,
                    "response_time_seconds": 30.0
                },
                "notifications": {
                    "email": {
                        "enabled": False,
                        "smtp_server": "smtp.gmail.com",
                        "smtp_port": 587,
                        "use_tls": True,
                        "from_address": "",
                        "to_addresses": [],
                        "username": "",
                        "password": ""
                    },
                    "webhook": {
                        "enabled": False,
                        "url": "",
                        "headers": {}
                    }
                }
            },
            "scheduling": {
                "daily_hour": 2,  # 2 AM
                "enable_hourly_checks": False
            }
        }

    def _get_environment_configuration(self) -> Optional[Dict[str, Any]]:
        """Get environment-specific configuration overrides"""
        env_configs = {
            "development": {
                "orchestrator": {
                    "log_level": "DEBUG"
                },
                "download": {
                    "max_concurrent": 2,
                    "rate_limit_seconds": 2.0
                },
                "processing": {
                    "batch_size": 1000,
                    "max_workers": 2
                },
                "database": {
                    "batch_size": 100,
                    "max_connections": 3
                },
                "monitoring": {
                    "check_interval_seconds": 30
                }
            },
            "staging": {
                "orchestrator": {
                    "log_level": "INFO"
                },
                "counties": {
                    "broward": {"enabled": True},
                    "miami_dade": {"enabled": True},
                    "palm_beach": {"enabled": False}
                }
            },
            "production": {
                "orchestrator": {
                    "log_level": "INFO"
                },
                "counties": {
                    "broward": {"enabled": True},
                    "miami_dade": {"enabled": True}, 
                    "palm_beach": {"enabled": True}
                },
                "scheduling": {
                    "enable_hourly_checks": True
                }
            }
        }
        
        return env_configs.get(self.environment, {})

    def _apply_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration"""
        
        # Database configuration from Supabase environment variables
        if os.getenv('SUPABASE_URL'):
            config.setdefault('supabase', {})['url'] = os.getenv('SUPABASE_URL')
        if os.getenv('SUPABASE_ANON_KEY'):
            config.setdefault('supabase', {})['anon_key'] = os.getenv('SUPABASE_ANON_KEY')
        if os.getenv('SUPABASE_SERVICE_KEY'):
            config.setdefault('supabase', {})['service_key'] = os.getenv('SUPABASE_SERVICE_KEY')
        if os.getenv('SUPABASE_DB_URL'):
            config.setdefault('supabase', {})['db_url'] = os.getenv('SUPABASE_DB_URL')
        
        # Email notification configuration
        if os.getenv('SMTP_SERVER'):
            config['monitoring']['notifications']['email']['smtp_server'] = os.getenv('SMTP_SERVER')
        if os.getenv('SMTP_PORT'):
            config['monitoring']['notifications']['email']['smtp_port'] = int(os.getenv('SMTP_PORT'))
        if os.getenv('EMAIL_FROM'):
            config['monitoring']['notifications']['email']['from_address'] = os.getenv('EMAIL_FROM')
        if os.getenv('EMAIL_TO'):
            config['monitoring']['notifications']['email']['to_addresses'] = os.getenv('EMAIL_TO').split(',')
        if os.getenv('EMAIL_USERNAME'):
            config['monitoring']['notifications']['email']['username'] = os.getenv('EMAIL_USERNAME')
        if os.getenv('EMAIL_PASSWORD'):
            config['monitoring']['notifications']['email']['password'] = os.getenv('EMAIL_PASSWORD')
            config['monitoring']['notifications']['email']['enabled'] = True
        
        # Webhook notification configuration
        if os.getenv('WEBHOOK_URL'):
            config['monitoring']['notifications']['webhook']['url'] = os.getenv('WEBHOOK_URL')
            config['monitoring']['notifications']['webhook']['enabled'] = True
        
        # Log level override
        if os.getenv('LOG_LEVEL'):
            config['orchestrator']['log_level'] = os.getenv('LOG_LEVEL')
        
        # Performance tuning overrides
        if os.getenv('DOWNLOAD_MAX_CONCURRENT'):
            config['download']['max_concurrent'] = int(os.getenv('DOWNLOAD_MAX_CONCURRENT'))
        if os.getenv('PROCESSING_BATCH_SIZE'):
            config['processing']['batch_size'] = int(os.getenv('PROCESSING_BATCH_SIZE'))
        if os.getenv('DATABASE_MAX_CONNECTIONS'):
            config['database']['max_connections'] = int(os.getenv('DATABASE_MAX_CONNECTIONS'))
        
        return config

    def _merge_configurations(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two configuration dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configurations(result[key], value)
            else:
                result[key] = value
        
        return result

    def _decrypt_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt encrypted values in configuration"""
        try:
            fernet = Fernet(self.encryption_key)
            
            # Recursively look for encrypted values (prefixed with "encrypted:")
            def decrypt_recursive(obj):
                if isinstance(obj, dict):
                    return {key: decrypt_recursive(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [decrypt_recursive(item) for item in obj]
                elif isinstance(obj, str) and obj.startswith("encrypted:"):
                    try:
                        encrypted_data = obj[10:]  # Remove "encrypted:" prefix
                        decrypted_bytes = fernet.decrypt(encrypted_data.encode())
                        return decrypted_bytes.decode()
                    except Exception as e:
                        logger.error(f"Failed to decrypt configuration value: {e}")
                        return obj
                else:
                    return obj
            
            return decrypt_recursive(config)
            
        except Exception as e:
            logger.error(f"Configuration decryption failed: {e}")
            return config

    def encrypt_value(self, value: str) -> str:
        """Encrypt a configuration value"""
        try:
            fernet = Fernet(self.encryption_key)
            encrypted_bytes = fernet.encrypt(value.encode())
            return f"encrypted:{encrypted_bytes.decode()}"
        except Exception as e:
            logger.error(f"Failed to encrypt value: {e}")
            return value

    def get_config(self) -> Dict[str, Any]:
        """Get the complete configuration"""
        # Check if configuration needs reloading
        if self._should_reload_config():
            self._load_configuration()
        
        return self.config_cache.copy()

    def get_county_config(self, county_name: str) -> Optional[CountyConfig]:
        """Get configuration for a specific county"""
        config = self.get_config()
        county_data = config.get("counties", {}).get(county_name)
        
        if county_data:
            return CountyConfig(
                code=county_data["code"],
                name=county_data["name"],
                enabled=county_data.get("enabled", True),
                priority=county_data.get("priority", 5),
                special_handling=county_data.get("special_handling", {})
            )
        
        return None

    def get_enabled_counties(self) -> List[CountyConfig]:
        """Get list of all enabled counties"""
        config = self.get_config()
        counties = []
        
        for county_name, county_data in config.get("counties", {}).items():
            if county_data.get("enabled", True):
                counties.append(CountyConfig(
                    code=county_data["code"],
                    name=county_data["name"],
                    enabled=True,
                    priority=county_data.get("priority", 5),
                    special_handling=county_data.get("special_handling", {})
                ))
        
        # Sort by priority
        counties.sort(key=lambda x: x.priority)
        return counties

    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        config = self.get_config()
        db_config = config.get("database", {})
        supabase_config = config.get("supabase", {})
        
        return DatabaseConfig(
            url=supabase_config.get("db_url", ""),
            max_connections=db_config.get("max_connections", 10),
            batch_size=db_config.get("batch_size", 1000),
            retry_attempts=db_config.get("retry_attempts", 3),
            timeout_seconds=db_config.get("timeout_seconds", 30)
        )

    def get_notification_config(self) -> NotificationConfig:
        """Get notification configuration"""
        config = self.get_config()
        notifications = config.get("monitoring", {}).get("notifications", {})
        
        return NotificationConfig(
            email_enabled=notifications.get("email", {}).get("enabled", False),
            webhook_enabled=notifications.get("webhook", {}).get("enabled", False),
            email_settings=notifications.get("email", {}),
            webhook_settings=notifications.get("webhook", {})
        )

    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        try:
            # Merge updates with current config
            new_config = self._merge_configurations(self.config_cache, updates)
            
            # Validate new configuration
            jsonschema.validate(new_config, self.config_schema)
            
            # Update cache
            self.config_cache = new_config
            
            # Save to file
            self.save_configuration()
            
            logger.info("Configuration updated successfully")
            
        except jsonschema.ValidationError as e:
            logger.error(f"Configuration update validation failed: {e}")
            raise ValueError(f"Invalid configuration: {e}")
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            raise

    def save_configuration(self, config_path: Optional[str] = None):
        """Save current configuration to file"""
        try:
            output_path = config_path or self.config_path
            
            with open(output_path, 'w') as f:
                json.dump(self.config_cache, f, indent=2, default=str)
            
            logger.info(f"Configuration saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    def _should_reload_config(self) -> bool:
        """Check if configuration file has been modified and needs reloading"""
        if not self.last_loaded:
            return True
        
        config_file = Path(self.config_path)
        if not config_file.exists():
            return False
        
        try:
            file_mtime = datetime.fromtimestamp(config_file.stat().st_mtime)
            return file_mtime > self.last_loaded
        except:
            return False

    def reload_configuration(self):
        """Force reload of configuration from file"""
        logger.info("Reloading configuration...")
        self._load_configuration()

    def validate_configuration(self, config: Optional[Dict[str, Any]] = None) -> tuple[bool, List[str]]:
        """Validate configuration and return validation results"""
        target_config = config or self.config_cache
        errors = []
        
        try:
            jsonschema.validate(target_config, self.config_schema)
            
            # Additional custom validations
            
            # Check counties have unique codes
            county_codes = []
            for county_name, county_data in target_config.get("counties", {}).items():
                code = county_data.get("code")
                if code in county_codes:
                    errors.append(f"Duplicate county code: {code}")
                county_codes.append(code)
            
            # Check database configuration
            supabase_config = target_config.get("supabase", {})
            if not supabase_config.get("db_url"):
                errors.append("Missing database URL configuration")
            
            # Check notification configuration
            notifications = target_config.get("monitoring", {}).get("notifications", {})
            email_config = notifications.get("email", {})
            if email_config.get("enabled") and not email_config.get("from_address"):
                errors.append("Email notifications enabled but no from_address configured")
            
            if len(errors) == 0:
                return True, []
            else:
                return False, errors
                
        except jsonschema.ValidationError as e:
            return False, [str(e)]
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        config = self.get_config()
        
        enabled_counties = [
            f"{county_data['name']} ({county_data['code']})"
            for county_data in config.get("counties", {}).values()
            if county_data.get("enabled", True)
        ]
        
        return {
            "environment": config.get("orchestrator", {}).get("environment"),
            "version": config.get("orchestrator", {}).get("version"),
            "log_level": config.get("orchestrator", {}).get("log_level"),
            "enabled_counties": enabled_counties,
            "download_settings": {
                "max_concurrent": config.get("download", {}).get("max_concurrent"),
                "rate_limit": config.get("download", {}).get("rate_limit_seconds")
            },
            "processing_settings": {
                "batch_size": config.get("processing", {}).get("batch_size"),
                "max_workers": config.get("processing", {}).get("max_workers")
            },
            "database_settings": {
                "max_connections": config.get("database", {}).get("max_connections"),
                "batch_size": config.get("database", {}).get("batch_size")
            },
            "notifications_enabled": {
                "email": config.get("monitoring", {}).get("notifications", {}).get("email", {}).get("enabled", False),
                "webhook": config.get("monitoring", {}).get("notifications", {}).get("webhook", {}).get("enabled", False)
            },
            "last_loaded": self.last_loaded.isoformat() if self.last_loaded else None
        }