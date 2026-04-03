# UI Architecture & Layout Diagram

## Visual Component Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         StageProgressBar                                 │
│  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐                           │
│  │  📋  │───│  💬  │───│  🚀  │───│  ✓   │                           │
│  │Class │   │Resp. │   │Escal.│   │Close │                           │
│  └──────┘    └──────┘    └──────┘    └──────┘                           │
└─────────────────────────────────────────────────────────────────────────┘
│
├─ LEFT SIDEBAR (300px)    ├─ CENTER (1fr)              ├─ RIGHT (320px)
│                          │                            │
├─────────────────────┐   ├────────────────────────┐   ├──────────────────┐
│ FilterButtons       │   │ TicketDetail           │   │PerformanceMetrics│
├─────────────────────┤   │                        │   ├──────────────────┤
│ [ All    ]          │   │ Ticket Info:           │   │ Reward Score     │
│ [ Easy   ]          │   │ ─────────────────────  │   │    0.72          │
│ [ Medium ]          │   │ ID: 24567              │   ├──────────────────┤
│ [ Hard   ]          │   │ Category: Refund Req   │   │ Progress:        │
├─────────────────────┤   │ Customer: John Smith   │   │ ✓ Classification│
│ TicketList          │   │ Issue: Item damaged... │   │ ⚠ Pending Reply │
├─────────────────────┤   ├────────────────────────┤   │ ✕ Escalation... │
│ #24567              │   │ Agent Conversation     │   ├──────────────────┤
│ [Easy] Refund       │   │ ─────────────────────  │   │ Policy:          │
│ 👤 John Smith       │   │ Agent: How can I...    │   │ Refunds: 7 days  │
│ Item damaged...     │   │ Customer: Damaged...   │   │ Status: Progress │
├─────────────────────┤   │ [Reply textarea]       │   └──────────────────┘
│ #24568              │   │ [Submit]               │
│ [Medium] Return     │   └────────────────────────┘
│ 👤 Sarah Johnson    │
│ Wrong size...       │
├─────────────────────┤
│ #24569              │
│ [Medium] Account    │
│ 👤 Mike Williams    │
│ Cannot access...    │
├─────────────────────┤
│ #24570              │
│ [Hard] Delivery     │
│ 👤 Emily Brown      │
│ Package lost...     │
└─────────────────────┘
```

---

## Component Hierarchy

```
Dashboard
├── StageProgressBar
│   ├── Stage Circle 1: Classify
│   ├── Connector Line
│   ├── Stage Circle 2: Respond
│   ├── Connector Line
│   ├── Stage Circle 3: Escalate
│   ├── Connector Line
│   └── Stage Circle 4: Close
│
├── Left Sidebar (flexbox column)
│   ├── FilterButtons
│   │   ├── Button: All
│   │   ├── Button: Easy
│   │   ├── Button: Medium
│   │   └── Button: Hard
│   │
│   └── TicketList
│       ├── Ticket Item 1
│       ├── Ticket Item 2
│       ├── Ticket Item 3
│       └── Ticket Item 4
│
├── Center Content
│   └── TicketDetail
│       ├── Ticket Info Section
│       │   ├── ID
│       │   ├── Category
│       │   ├── Customer
│       │   ├── Issue
│       │   └── Status
│       │
│       └── Conversation Section
│           ├── Message (Agent)
│           ├── Message (Customer)
│           └── Reply Input
│
└── Right Sidebar
    └── PerformanceMetrics
        ├── Score Card
        ├── Checklist Section
        └── Policy Section
```

---

## Grid Layout (Desktop - 1600px+)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Full Width: 1600px                               │
├────────────┬────────────────────────────┬──────────────────────────┤
│  300px     │         1fr                │         320px            │
│ (Sidebar)  │      (MainContent)         │    (RightSidebar)        │
│            │                            │                          │
│  20px gap  │       20px gap             │       20px gap           │
└────────────┴────────────────────────────┴──────────────────────────┘
```

---

## Responsive Breakpoints

### 1. Desktop (1200px - 1600px)
```
Grid: [300px | 1fr | 320px]
Layout: 3 columns
Stage Bar: Full width at top
Tickets: Scrollable list
```

### 2. Tablet (768px - 992px)
```
Grid: [1fr]
Layout: Single column, sidebar becomes grid
Stage Bar: Full width
Filters & Tickets: 2 columns at top
Main: Full width below
Metrics: Across bottom
```

### 3. Mobile (< 768px)
```
Grid: [1fr]
Layout: Single column, fully stacked
Stage Bar: Circles may stack vertically
Filters: Stack vertically or horizontal scroll
Tickets: Full width list
Main: Full width
Metrics: Full width at bottom
```

---

## State Management Flow

```
Dashboard Component
│
├─ State: selectedFilter ('all' | 'easy' | 'medium' | 'hard')
│  │
│  └─→ FilterButtons.onFilterChange()
│      └─→ TicketList filter prop updates
│          └─→ List re-renders with filtered tickets
│
├─ State: selectedTicket (ticket object | null)
│  │
│  ├─→ TicketList.onSelectTicket()
│  │   └─→ Updates selectedTicket state
│  │
│  ├─→ TicketDetail.ticket prop
│  │   └─→ Shows details or empty state
│  │
│  └─→ PerformanceMetrics.ticket prop
│      └─→ Shows metrics or empty state
│
└─ State: currentStage (0 | 1 | 2 | 3)
   │
   └─→ StageProgressBar.currentStage prop
       └─→ Highlights active stage
```

---

## Color Scheme

| Element | Color | Usage |
|---------|-------|-------|
| Easy | #27ae60 (Green) | Easy difficulty badge |
| Medium | #f39c12 (Orange) | Medium difficulty badge |
| Hard | #e74c3c (Red) | Hard difficulty badge |
| Primary Action | #3b82f6 (Blue) | Active stages, selected tickets |
| Success | #27ae60 (Green) | Correct classification ✓ |
| Warning | #f39c12 (Orange) | Pending actions ⚠ |
| Error | #e74c3c (Red) | Errors/escalations needed ✕ |
| Background | #ecf0f1 → #d5dbdb (Gradient) | Page background |
| Card Background | #ffffff (White) | Component cards |

---

## Interaction Flow

### 1. User Clicks Filter Button
```
User clicks "Medium" button
    ↓
FilterButtons.onFilterChange('medium')
    ↓
Dashboard state: selectedFilter = 'medium'
    ↓
TicketList re-renders with filtered={'medium'}
    ↓
Only medium tickets display
```

### 2. User Selects a Ticket
```
User clicks a ticket in TicketList
    ↓
TicketList.onSelectTicket(ticket)
    ↓
Dashboard state: selectedTicket = ticket object
    ↓
TicketDetail receives selectedTicket prop
PerformanceMetrics receives selectedTicket prop
    ↓
Both panels update with ticket info
```

### 3. Stage Progress Updates
```
Agent takes action (e.g., "classify_ticket")
    ↓
Dashboard: setCurrentStage(1)
    ↓
StageProgressBar receives currentStage={1}
    ↓
Circles 0 and 1 highlight blue
Line 0→1 becomes active
```

---

## CSS Module Organization

```
Each component has 2 files:
├─ Component.js        (React logic)
└─ Component.module.css (Scoped styles)

Benefits:
✓ No style conflicts
✓ Easy to maintain
✓ Component-specific styling
✓ Easy to modify individual components
✓ CSS class names auto-scoped
```

---

## Mock Data Example

```javascript
{
  "id": 24567,
  "category": "Refund Request",
  "customer": "John Smith",
  "issue": "The item I received is damaged. I want a refund!",
  "difficulty": "easy",
  "status": "open"
}
```

---

## Key Design Principles

1. **Visual Feedback**: Every interaction has visual response
2. **Clear Hierarchy**: Important info is prominent
3. **Responsive**: Works on all screen sizes
4. **Accessibility**: Good contrast, readable fonts
5. **Performance**: CSS modules for optimization
6. **Modularity**: Each component is independent
7. **Reusability**: Components can be reused elsewhere

---

## File Size Reference

| File | Type | Size |
|------|------|------|
| Dashboard.js | React + State | ~2KB |
| StageProgressBar.js | React | ~1.5KB |
| FilterButtons.js | React | ~1.2KB |
| TicketList.js | React + Data | ~2.5KB |
| TicketDetail.js | React | ~2.8KB |
| PerformanceMetrics.js | React | ~1.8KB |
| Combined CSS Modules | CSS | ~8KB |
| **Total** | | ~20KB |

---

**Created**: April 3, 2026  
**Status**: UI Architecture Complete

