/**
 * ConcordBroker Standardized Error Codes
 * Format: CB-XXXX-YYY
 * Generated: 2025-09-21T20:28:11.984658
 */

export enum ErrorCategory {
  AUTH = 1,  // Authentication & Authorization
  DB = 2,  // Database Operations
  API = 3,  // API & Network
  BIZ = 4,  // Business Logic
  FILE = 5,  // File System
  EXT = 6,  // External Services
  VAL = 7,  // Validation
  SYS = 8,  // System/Infrastructure
  UNK = 9,  // Unknown/Unhandled
}

export enum ErrorCode {
  AUTH_INVALID_TOKEN = 'CB-1000',
  AUTH_SESSION_EXPIRED = 'CB-1001',
  AUTH_INSUFFICIENT_PERMISSIONS = 'CB-1002',
  DB_CONNECTION_FAILED = 'CB-2000',
  DB_QUERY_ERROR = 'CB-2001',
  DB_TRANSACTION_FAILED = 'CB-2002',
  API_ENDPOINT_NOT_FOUND = 'CB-3000',
  API_REQUEST_TIMEOUT = 'CB-3001',
  API_RATE_LIMIT_EXCEEDED = 'CB-3002',
  BIZ_INVALID_STATE = 'CB-4000',
  BIZ_OPERATION_NOT_ALLOWED = 'CB-4001',
  BIZ_RESOURCE_CONFLICT = 'CB-4002',
  VAL_REQUIRED_FIELD_MISSING = 'CB-7000',
  VAL_INVALID_FORMAT = 'CB-7001',
  VAL_VALUE_OUT_OF_RANGE = 'CB-7002',
}

export class ConcordError extends Error {
  code: string;
  category: ErrorCategory;
  statusCode: number;
  details?: any;

  constructor(
    code: string,
    message: string,
    statusCode: number = 500,
    details?: any
  ) {
    super(message);
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
    this.category = this.getCategoryFromCode(code);
    this.name = 'ConcordError';
  }

  private getCategoryFromCode(code: string): ErrorCategory {
    // Extract category from format CB-XXXX where X is category digit
    const match = code.match(/CB[_-](\d)/);
    if (match) {
      const categoryCode = parseInt(match[1]);
      return categoryCode as ErrorCategory;
    }
    return ErrorCategory.UNK;
  }

  toJSON() {
    return {
      code: this.code,
      message: this.message,
      category: this.category,
      statusCode: this.statusCode,
      details: this.details
    };
  }
}

export const ErrorMessages: Record<string, string> = {
  'CB-1000': 'Invalid authentication token',
  'CB-1001': 'Session has expired',
  'CB-1002': 'Insufficient permissions',
  'CB-2000': 'Database connection failed',
  'CB-2001': 'Database query error',
  'CB-2002': 'Transaction failed',
  'CB-3000': 'API endpoint not found',
  'CB-3001': 'Request timeout',
  'CB-3002': 'Rate limit exceeded',
  'CB-4000': 'Invalid business state',
  'CB-4001': 'Operation not allowed',
  'CB-4002': 'Resource conflict',
  'CB-7000': 'Required field is missing',
  'CB-7001': 'Invalid data format',
  'CB-7002': 'Value is out of acceptable range',
};

// Helper function to create standardized errors
export function createError(
  code: ErrorCode,
  customMessage?: string,
  statusCode?: number,
  details?: any
): ConcordError {
  const message = customMessage || ErrorMessages[code] || 'An error occurred';
  return new ConcordError(code, message, statusCode, details);
}
