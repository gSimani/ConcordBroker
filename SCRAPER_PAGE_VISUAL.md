# 🖥️ Manual Scraper Controls - Page Layout

## Page Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                     HEADER (Dark Navy/Gray)                     │
│  🛡️ Data Scraper Management            [← Back to Admin]       │
│  Manual control for automated data extraction workflows         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  📋 Data Scraper Controls                                       │
│  Manually trigger scheduled data extraction workflows           │
│                                                                 │
│  Dry Run Mode  [🔵━━━━○] (No database changes)                │
│                                                                 │
│  ℹ️  [INFO BOX - Blue]                                          │
│  These scrapers run automatically on schedule. Manual triggers  │
│  are for testing or forcing immediate updates. View logs in     │
│  GitHub Actions after triggering.                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────┐  ┌──────────────────────────────┐
│  🏢 Property Data Update     │  │  🗄️  Sunbiz Data Update     │
│  (Dark Gray Card)            │  │  (Blue Card)                 │
│                              │  │                              │
│  Updates Florida property    │  │  Updates Florida business    │
│  data from 67 counties       │  │  entity data from SFTP       │
│                              │  │                              │
│  ⏰ Daily at 2:00 AM EST     │  │  ⏰ Daily at 3:00 AM EST     │
│                              │  │                              │
│  ✅ [SUCCESS MESSAGE]        │  │  ❌ [ERROR MESSAGE]          │
│  Workflow triggered!         │  │  (if applicable)             │
│  (Dry Run Mode)              │  │                              │
│                              │  │                              │
│  Last: Nov 6, 12:15:30 PM    │  │  Last: [never]               │
│                              │  │                              │
│  [📥 Trigger Dry Run]        │  │  [📥 Trigger Dry Run]        │
│  (Full width button)         │  │  (Full width button)         │
│                              │  │                              │
│  View Workflow Logs →        │  │  View Workflow Logs →        │
│                              │  │                              │
└──────────────────────────────┘  └──────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  📚 About Data Scrapers                                         │
│                                                                 │
│  Property Data Update: Downloads and processes data from        │
│  Florida Revenue Portal. Covers 268 files across 67 counties   │
│  including property details, sales history, and valuations.     │
│                                                                 │
│  Sunbiz Data Update: Connects to Florida Department of State   │
│  SFTP server to download daily business entity files            │
│  (corporate filings, events, and fictitious names).             │
│                                                                 │
│  Dry Run Mode: When enabled, the scraper will execute all      │
│  steps except database writes. Useful for testing.              │
│                                                                 │
│  Note: Workflows may take 30 minutes to 3 hours to complete.   │
│  Check your email for completion notifications.                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Color Scheme

- **Header**: Dark navy gradient (#2c3e50 → #34495e)
- **Property Card**: Dark gray with light gray background
- **Sunbiz Card**: Blue with light blue background
- **Toggle ON**: Blue (#3498db)
- **Toggle OFF**: Gray (#bdc3c7)
- **Success**: Green background with green border
- **Error**: Red background with red border
- **Pending**: Blue background with blue border + spinner

## Interactive Elements

### Dry Run Toggle
```
OFF: Dry Run Mode  [○━━━━━]
ON:  Dry Run Mode  [━━━━━🔵] (No database changes)
```

### Button States

**Default**:
```
┌─────────────────────────┐
│  📥 Trigger Dry Run     │
└─────────────────────────┘
```

**Loading**:
```
┌─────────────────────────┐
│  🔄 Triggering...       │  (spinner animating)
└─────────────────────────┘
```

**Disabled** (during execution):
```
┌─────────────────────────┐
│  📥 Trigger Dry Run     │  (grayed out, not clickable)
└─────────────────────────┘
```

### Status Messages

**Success (Green)**:
```
┌──────────────────────────────────────────────┐
│ ✅  Workflow triggered successfully!         │
│     (Dry Run Mode)                           │
└──────────────────────────────────────────────┘
```

**Error (Red)**:
```
┌──────────────────────────────────────────────┐
│ ❌  Failed to trigger workflow: 403 Forbidden│
└──────────────────────────────────────────────┘
```

**Pending (Blue)**:
```
┌──────────────────────────────────────────────┐
│ 🔄  Triggering workflow...                   │
└──────────────────────────────────────────────┘
```

## Responsive Layout

**Desktop (2 columns)**:
```
[Property Card]  [Sunbiz Card]
```

**Tablet/Mobile (1 column)**:
```
[Property Card]
[Sunbiz Card]
```

## Animation

- Cards fade in with stagger effect (0.1s delay between each)
- Hover effect: slight lift with shadow
- Button hover: darker background
- Status messages: smooth fade in/out
- Spinner: continuous rotation

## Actual Dimensions

- **Max width**: 7xl (80rem / 1280px)
- **Card spacing**: 6 units (1.5rem / 24px)
- **Button height**: Standard button height (~40px)
- **Card padding**: 6 units (1.5rem / 24px)
- **Header height**: 16 units (4rem / 64px)
