# Customer Support UI Implementation Guide

## Overview

This document describes the React components and layout structure for the OpenEnv customer support AI environment UI. The UI has been completely redesigned based on your requirements.

---

## ✨ Key Changes Made

### Before (Original)
- Basic template with next.js starter code
- No custom components
- No ticket management

### After (New Design)
- ✅ **Stage Progress Bar** at the top showing workflow steps (Classify → Respond → Escalate → Close)
- ✅ **Filter Buttons** on the left (All, Easy, Medium, Hard)
- ✅ **Dynamic Ticket List** that updates when filters change
- ✅ **Ticket Details Panel** in the center
- ✅ **Performance Metrics** on the right sidebar
- ✅ **Agent Conversation** panel with message history
- ✅ **Responsive Design** - works on desktop, tablet, and mobile

---

## 📁 Component Structure

```
src/components/
├── Dashboard.js                    # Main container component
├── Dashboard.module.css            # Main layout styling
├── StageProgressBar.js             # Top progress bar with workflow stages
├── StageProgressBar.module.css     # Stage progress styling
├── FilterButtons.js                # Left sidebar filter buttons
├── FilterButtons.module.css        # Filter button styling
├── TicketList.js                   # Ticket list panel
├── TicketList.module.css           # Ticket list styling
├── TicketDetail.js                 # Center panel with ticket & conversation
├── TicketDetail.module.css         # Ticket detail styling
├── PerformanceMetrics.js           # Right sidebar metrics
└── PerformanceMetrics.module.css   # Performance metrics styling
```

---

## 🎯 Component Details

### 1. **Dashboard.js** (Main Container)
Orchestrates all components and manages global state:
- `selectedFilter`: Current difficulty filter ('all', 'easy', 'medium', 'hard')
- `selectedTicket`: Currently selected ticket object
- `currentStage`: Current workflow stage (0-3)

**Layout**: 
```
[StageProgressBar across full width]
[FilterButtons | TicketDetail | PerformanceMetrics]
```

---

### 2. **StageProgressBar.js** (Top Navigation)
Displays the 4 workflow stages in circles connected by lines.

**Features**:
- 📋 **Classify** - Step 1: Identify issue type
- 💬 **Respond** - Step 2: Send customer response
- 🚀 **Escalate** - Step 3: Escalate if needed
- ✓ **Close** - Step 4: Mark as resolved

**Props**:
- `currentStage` (0-3): Highlights completed stages

**Styling**:
- Circles become blue when active
- Connecting lines fill as stages complete
- Responsive on mobile (circles stack vertically)

---

### 3. **FilterButtons.js** (Left Sidebar - Top)
Filter tickets by difficulty level.

**Features**:
- 4 buttons: "All", "Easy", "Medium", "Hard"
- Each button has unique color when selected
- Smooth hover effects with slide animation

**Props**:
- `selectedFilter`: Current active filter
- `onFilterChange()`: Callback when filter changes

**Difficulty Colors**:
- All: Gray (#4a5a7a)
- Easy: Green (#27ae60)
- Medium: Orange (#f39c12)
- Hard: Red (#e74c3c)

---

### 4. **TicketList.js** (Left Sidebar - Bottom)
Dynamic list of tickets filtered by selected difficulty.

**Features**:
- Scrollable list
- Click to select ticket
- Shows ticket ID, category, customer name, issue description
- Difficulty badge with color coding
- Highlights selected ticket with blue border

**Mock Data**:
```javascript
mockTickets = {
  all: [...],    // All 4 tickets
  easy: [...],   // Easy tickets only
  medium: [...], // Medium tickets only
  hard: [...]    // Hard tickets only
}
```

**Props**:
- `filter`: Current filter ('all', 'easy', 'medium', 'hard')
- `selectedTicket`: Currently selected ticket
- `onSelectTicket()`: Callback when ticket is selected

---

### 5. **TicketDetail.js** (Center Panel)
Shows full ticket details and agent-customer conversation.

**Sections**:

#### A. Ticket Information
- Ticket ID
- Category (Refund Request, Return Request, etc.)
- Customer Name
- Issue Description
- Status Badge

#### B. Agent Conversation
- Message history with role-based styling
- Agent messages: Green background
- Customer messages: Yellow background
- Reply input textarea

**Props**:
- `ticket`: Selected ticket object or null

**Features**:
- Empty state when no ticket selected
- Scrollable conversation history
- Responsive textarea for replies

---

### 6. **PerformanceMetrics.js** (Right Sidebar)
Shows scoring and progress information.

**Display Elements**:

#### A. Reward Score Card
- Large score display (0.72 in example)
- Gradient background

#### B. Progress Checklist
- ✓ (Green) Correct Classification
- ⚠ (Orange) Pending Reply
- ✕ (Red) Escalation Needed

#### C. Policy Information
- Policy text ("Refunds within 7 days")
- Current status ("In Progress")

**Props**:
- `ticket`: Selected ticket or null

---

## 🎨 Styling System

### CSS Modules
Each component has its own `.module.css` file for scoped styling (prevents conflicts).

### Color Palette
```css
--primary: #3b82f6          /* Blue */
--primary-dark: #1e40af     /* Dark Blue */
--success: #27ae60          /* Green */
--warning: #f39c12          /* Orange */
--danger: #e74c3c           /* Red */
```

### Responsive Breakpoints
- **Desktop**: 1600px max (3-column grid)
- **Tablet**: 992px max (1-column with sidebar on top)
- **Mobile**: 768px max (stacked layout)

---

## 🔄 Data Flow

```
Dashboard (State Management)
    ↓
    ├─→ StageProgressBar (currentStage)
    │
    ├─→ FilterButtons (selectedFilter) ←→ TicketList (filter)
    │                                         ↓
    ├─→ TicketDetail (selectedTicket)
    │
    └─→ PerformanceMetrics (selectedTicket)
```

---

## 📝 Mock Data Structure

### Ticket Object
```javascript
{
  id: 24567,
  category: "Refund Request",
  customer: "John Smith",
  issue: "Item damaged, requesting refund",
  difficulty: "easy",
  status: "open"
}
```

### Current Mock Tickets
- **Easy**: 1 ticket (Refund Request)
- **Medium**: 2 tickets (Return Request, Account Issue)
- **Hard**: 1 ticket (Delivery Problem)

---

## ⚡ Usage Example

```javascript
import Dashboard from '@/components/Dashboard';

export default function Home() {
  return <Dashboard />;
}
```

The Dashboard component manages all state internally. Just import and use!

---

## 🔧 How to Modify

### Change Filter Options
Edit `FilterButtons.js`:
```javascript
const difficultyLevels = [
  { id: 'all', label: 'All', color: '#4a5a7a' },
  // Add more options here
];
```

### Add More Ticket Fields
Edit mock data in `TicketList.js`:
```javascript
const mockTickets = {
  easy: [
    {
      id: 24567,
      category: 'Refund Request',
      // Add more fields here
    }
  ]
};
```

### Update Stage Names
Edit `StageProgressBar.js`:
```javascript
const stages = [
  { id: 1, label: 'Classify', icon: '📋' },
  { id: 2, label: 'Respond', icon: '💬' },
  // Modify label and icon
];
```

### Change Colors
Edit the `.module.css` files or update `globals.css` CSS variables.

---

## 📱 Responsive Features

### Desktop (1600px+)
- 3-column layout: [Left Sidebar] [Main Content] [Right Sidebar]
- Wide comfortable spacing

### Tablet (992-1200px)
- Still 3 columns but more compressed
- Sidebar buttons stack horizontally

### Mobile (< 768px)
- Single column layout
- All content stacked vertically
- Filters and tickets side-by-side at top
- Main content below
- Metrics at bottom

---

## 🚀 Next Steps for Integration

Once the backend environment is ready:

1. **Replace mock data** in `TicketList.js` with real API calls:
   ```javascript
   const response = await fetch('/api/tickets?filter=' + filter);
   const tickets = await response.json();
   ```

2. **Connect stage updates** in `Dashboard.js` to track agent actions:
   ```javascript
   const handleAction = (action) => {
     if (action === 'classify_ticket') setCurrentStage(1);
     // etc.
   };
   ```

3. **Send actions** to backend environment in `TicketDetail.js`:
   ```javascript
   const handleSubmitReply = async (reply) => {
     const result = await env.step({ action: 'respond', text: reply });
   };
   ```

4. **Update metrics** from environment rewards:
   ```javascript
   <PerformanceMetrics 
     ticket={selectedTicket}
     score={environmentReward}
     progress={agentActions}
   />
   ```

---

## 🎓 Educational Value

This UI is designed to:
- Show agent progress through the workflow visually
- Help users understand ticket classification
- Display penalties/rewards in real-time
- Make the agent's decision-making transparent

---

**Last Updated**: April 3, 2026  
**Status**: UI Components Complete - Ready for Backend Integration

