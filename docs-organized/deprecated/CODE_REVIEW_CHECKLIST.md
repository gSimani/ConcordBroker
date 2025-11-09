# Code Review Checklist
Based on Self-Improving Agent Principles (arxiv:2504.15228)

## 🔍 Pre-Review Checks

### Context Understanding
- [ ] **Read relevant documentation** before reviewing
- [ ] **Understand the problem** being solved
- [ ] **Check linked issues/tickets** for requirements
- [ ] **Review test cases** to understand expected behavior

## ✅ Core Principles Checklist

### 1. Incremental Development
- [ ] **Changes are minimal and focused** - no unnecessary modifications
- [ ] **Single responsibility** - PR addresses one specific issue/feature
- [ ] **No end-to-end implementations** - broken into reviewable chunks
- [ ] **Clear commit history** - atomic commits with descriptive messages

### 2. Code Quality
- [ ] **Follows existing patterns** - consistent with codebase conventions
- [ ] **DRY principle** - no duplicated code
- [ ] **Clear naming** - variables, functions, and classes are self-documenting
- [ ] **Comments explain WHY** not WHAT (code should be self-explanatory)

### 3. Atomic Tools & Functions
- [ ] **Each function does ONE thing** well
- [ ] **Clear input/output contracts** - type hints and validation
- [ ] **Comprehensive error handling** - all edge cases covered
- [ ] **No side effects** - functions are predictable and testable

### 4. Confidence & Safety

#### Confidence Thresholds
- [ ] **Confidence scoring implemented** where decisions are made
- [ ] **Escalation paths defined** for low-confidence operations (< 70%)
- [ ] **Risk assessment** for high-value operations (> $100k)
- [ ] **Human review triggers** properly configured

#### Safety Guardrails
- [ ] **Input validation** on all external data
- [ ] **No hardcoded secrets** or credentials
- [ ] **SQL injection prevention** - parameterized queries
- [ ] **Rate limiting** on external API calls
- [ ] **Timeout handling** for all async operations

### 5. Testing
- [ ] **Unit tests** for new functionality
- [ ] **Integration tests** for API endpoints
- [ ] **Edge cases tested** - null, empty, invalid inputs
- [ ] **Error scenarios tested** - network failures, timeouts
- [ ] **Test coverage** maintained or improved (target > 80%)

### 6. Performance
- [ ] **No N+1 queries** - efficient database access
- [ ] **Appropriate caching** - frequently accessed data cached
- [ ] **Async operations** where beneficial
- [ ] **Resource cleanup** - connections, files, memory
- [ ] **Performance impact assessed** - no significant degradation

### 7. Logging & Monitoring
- [ ] **Operation logging** - key actions logged with context
- [ ] **Error logging** - exceptions logged with stack traces
- [ ] **Decision logging** - agent decisions tracked with confidence
- [ ] **Metrics collection** - performance metrics recorded
- [ ] **Debug information** - sufficient for troubleshooting

## 🔐 Security Checklist

### Data Protection
- [ ] **PII handling** - personal data properly protected
- [ ] **Encryption** - sensitive data encrypted at rest and in transit
- [ ] **Access control** - proper authorization checks
- [ ] **Audit trail** - sensitive operations logged

### API Security
- [ ] **Authentication required** - all endpoints protected
- [ ] **Authorization verified** - user permissions checked
- [ ] **CORS configured** - appropriate origins allowed
- [ ] **Input sanitization** - all inputs cleaned and validated

## 📊 Database Operations

### Query Safety
- [ ] **Parameterized queries** - no string concatenation
- [ ] **Transaction handling** - proper rollback on errors
- [ ] **Index usage** - queries use appropriate indexes
- [ ] **Bulk operation limits** - large operations batched

### Data Integrity
- [ ] **Validation before write** - data consistency maintained
- [ ] **Cascading deletes** handled properly
- [ ] **Foreign key constraints** respected
- [ ] **Optimistic locking** where needed

## 🚀 Deployment Readiness

### Configuration
- [ ] **Environment variables** - no hardcoded config
- [ ] **Feature flags** - new features can be toggled
- [ ] **Backwards compatibility** - migrations safe
- [ ] **Rollback plan** - can revert if issues arise

### Documentation
- [ ] **API documentation** updated if endpoints changed
- [ ] **README updated** if setup/config changed
- [ ] **CHANGELOG entry** added for user-facing changes
- [ ] **Migration guide** if breaking changes

## 🤖 Agent-Specific Checks

### Agent Design
- [ ] **Clear agent boundaries** - well-defined responsibilities
- [ ] **Dependency management** - agents loosely coupled
- [ ] **Message contracts** - clear communication protocols
- [ ] **Failure handling** - graceful degradation

### Self-Improvement
- [ ] **Performance tracking** - metrics collected for analysis
- [ ] **Learning capability** - can improve from outcomes
- [ ] **Feedback loops** - results inform future decisions
- [ ] **Version control** - agent configurations versioned

## 📝 Final Review

### Code Review Metrics
- [ ] **Review thoroughness** - all changed files reviewed
- [ ] **Feedback addressed** - all comments resolved
- [ ] **Tests passing** - CI/CD pipeline green
- [ ] **No console.log/print** statements in production code

### Approval Criteria
- [ ] Follows all coding standards
- [ ] No critical security issues
- [ ] Performance acceptable
- [ ] Tests comprehensive
- [ ] Documentation complete

## 🎯 Scoring Guide

Rate each section 1-5:
- **5**: Exceptional - exceeds all standards
- **4**: Good - meets all requirements
- **3**: Acceptable - minor improvements needed
- **2**: Needs work - significant issues
- **1**: Unacceptable - major rework required

**Minimum score for approval: 3.5 average**

## 🔄 Continuous Improvement

After each review:
1. Update this checklist with new learnings
2. Share patterns that work well
3. Document anti-patterns to avoid
4. Track common issues for training

---

*Last Updated: Based on arxiv:2504.15228 - Self-Improving Coding Agent*