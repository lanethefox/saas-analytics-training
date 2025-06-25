# Entity Relationships & ID Allocation

## Entity Relationship Diagram

```
┌─────────────────┐
│    Accounts     │
│  (Customers)    │
│ ID: 1-150       │
└────────┬────────┘
         │ 1:N
    ┌────┴────┬─────────┬─────────────┐
    │         │         │             │
    ▼         ▼         ▼             ▼
┌──────────┐┌────────┐┌─────────┐┌──────────────┐
│Locations ││ Users  ││Subscrip-││Feature Usage │
│ID: 1-1000││ID:1-6k ││ tions   ││ID: 1-1M      │
└────┬─────┘└────────┘│ID: 1-200│└──────────────┘
     │ 1:N            └─────────┘
     ▼
┌──────────┐
│ Devices  │
│ID: 1-30k │
└────┬─────┘
     │ 1:N
     ▼
┌──────────────┐
│ Tap Events   │
│ID: 1-10M     │
└──────────────┘
```

## Foreign Key Relationships

### Primary Relationships
1. **Locations.account_id** → Accounts.id
2. **Devices.location_id** → Locations.id
3. **Devices.customer_id** → Accounts.id (denormalized)
4. **Users.customer_id** → Accounts.id
5. **Subscriptions.customer_id** → Accounts.id

### Event Relationships
1. **TapEvents.device_id** → Devices.id
2. **TapEvents.location_id** → Locations.id (denormalized)
3. **TapEvents.account_id** → Accounts.id (denormalized)
4. **FeatureUsage.user_id** → Users.id
5. **FeatureUsage.account_id** → Accounts.id (denormalized)
6. **PageViews.user_id** → Users.id
7. **UserSessions.user_id** → Users.id

## ID Allocation Strategy

### Sequential ID Ranges

| Entity | ID Range | Reserved | Notes |
|--------|----------|----------|-------|
| Accounts | 1-150 | 151-200 | Future growth buffer |
| Locations | 1-1,000 | 1,001-1,500 | ~800 expected |
| Devices | 1-30,000 | 30,001-35,000 | ~25,000 expected |
| Users | 1-6,000 | 6,001-7,000 | ~5,000 expected |
| Subscriptions | 1-200 | 201-300 | One per account + history |
| Tap Events | 1-10,000,000 | - | High volume transactional |
| Feature Usage | 1-1,000,000 | - | User activity tracking |
| Page Views | 1-2,000,000 | - | Web analytics |
| User Sessions | 1-500,000 | - | Session tracking |

### ID Generation Rules

1. **Accounts**: Sequential 1-150
   - Small accounts: 1-105
   - Medium accounts: 106-135
   - Large accounts: 136-147
   - Enterprise accounts: 148-150

2. **Locations**: Sequential within account ranges
   - Formula: `base_id + location_index`
   - Ensures consistent location IDs per account

3. **Devices**: Sequential within location ranges
   - Formula: `location_id * 100 + device_index`
   - Max 100 devices per location

4. **Users**: Sequential within account ranges
   - Admin users get lower IDs within account
   - Ensures predictable user ID patterns

## Data Integrity Rules

### Referential Integrity
- No orphaned records allowed
- All foreign keys must reference existing records
- Cascading relationships properly defined

### Business Logic Integrity
1. Each account must have at least one location
2. Each location must have at least one device
3. Each account must have at least one user
4. Each account must have exactly one active subscription
5. Device count must match subscription tier limits

### Temporal Integrity
1. Child records created after parent records
2. Events occur after device installation
3. User sessions start after user creation
4. Subscription start date after account creation

## Validation Queries

### Check Orphaned Devices
```sql
SELECT COUNT(*) as orphaned_devices
FROM devices d
LEFT JOIN locations l ON d.location_id = l.id
WHERE l.id IS NULL;
```

### Check Account Device Counts
```sql
SELECT a.id, a.name, 
       COUNT(DISTINCT d.id) as device_count,
       s.tier,
       CASE 
         WHEN s.tier = 'starter' AND COUNT(DISTINCT d.id) > 10 THEN 'OVER_LIMIT'
         WHEN s.tier = 'professional' AND COUNT(DISTINCT d.id) > 50 THEN 'OVER_LIMIT'
         WHEN s.tier = 'business' AND COUNT(DISTINCT d.id) > 200 THEN 'OVER_LIMIT'
         ELSE 'OK'
       END as status
FROM accounts a
JOIN locations l ON a.id = l.account_id
JOIN devices d ON l.id = d.location_id
JOIN subscriptions s ON a.id = s.customer_id AND s.status = 'active'
GROUP BY a.id, a.name, s.tier;
```

### Check Temporal Consistency
```sql
-- Devices created after locations
SELECT COUNT(*) as invalid_devices
FROM devices d
JOIN locations l ON d.location_id = l.id
WHERE d.created_at < l.created_at;

-- Events after device creation
SELECT COUNT(*) as invalid_events
FROM tap_events te
JOIN devices d ON te.device_id = d.id
WHERE te.timestamp < d.created_at;
```

## Mapping Tables

### Account Size Mapping
| Size | Account IDs | Location Count | Device Count |
|------|------------|----------------|--------------|
| Small | 1-105 | 1-2 | 5-20 |
| Medium | 106-135 | 3-10 | 30-200 |
| Large | 136-147 | 10-50 | 200-2,500 |
| Enterprise | 148-150 | 50-100 | 1,500-10,000 |

### Industry Mapping
| Industry | Percentage | Typical Patterns |
|----------|------------|------------------|
| Restaurant | 40% | High lunch/dinner peaks |
| Bar | 25% | Evening/night peaks |
| Stadium | 10% | Event-driven spikes |
| Hotel | 15% | Steady throughout day |
| Corporate | 10% | Business hours only |