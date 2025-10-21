# Testing the Refactored UI Pages

## ✅ Pages Successfully Launched

Both refactored UI pages are now running and ready for testing!

### 🏆 Tournament Page (Refactored)
- **URL**: http://localhost:8503
- **File**: `src/codexes/pages/21_Imprint_Ideas_Tournament_Refactored.py`
- **Status**: ✅ Running

### 🎨 Enhanced Imprint Creator (Refactored)
- **URL**: http://localhost:8505
- **File**: `src/codexes/pages/20_Enhanced_Imprint_Creator_Refactored.py`
- **Status**: ✅ Running

---

## 🧪 What to Test

### Tournament Page (Port 8503)

#### Tab 1: 🎯 Setup Tournament
- [ ] Upload CSV/Excel file with imprint ideas
- [ ] Check completeness analysis
- [ ] Create new tournament with configurable size (2-256)
- [ ] Verify tournament structure (byes for non-power-of-2)
- [ ] Check validation for total ideas matching tournament size

#### Tab 2: ⚔️ Run Tournament
- [ ] Add user ideas (name, charter, focus)
- [ ] Generate AI ideas (should create ImprintIdea objects)
- [ ] Start tournament (creates brackets using Tournament.start())
- [ ] Vote on matchups
- [ ] Advance rounds
- [ ] Complete tournament

#### Tab 3: 🏅 Results
- [ ] View tournament status
- [ ] See winner when complete
- [ ] Create imprint from winner

#### Tab 4: 💡 Generate Ideas
- [ ] Select focus areas
- [ ] Adjust innovation level
- [ ] Generate inspiration ideas
- [ ] View generated ideas

**Key Testing Points**:
- All operations should use `TournamentService`
- Domain objects (`Tournament`, `ImprintIdea`, `Matchup`) are used throughout
- No direct dictionary access
- Type-safe operations

---

### Enhanced Imprint Creator (Port 8505)

#### Tab 1: 🧙 Step-by-Step Wizard

**Step 1: Basic Info**
- [ ] Enter imprint name, publisher, tagline
- [ ] Enter charter and mission statement
- [ ] Enter contact email
- [ ] Click "Next" - should create BrandingSpecification object

**Step 2: Publisher Persona**
- [ ] Enter persona name and bio
- [ ] Select risk tolerance (Conservative/Moderate/Aggressive)
- [ ] Select decision style (Data-Driven/Intuitive/etc.)
- [ ] Select preferred topics and demographics
- [ ] Add vulnerabilities (optional)
- [ ] Click "Next" - should create PublisherPersona object

**Step 3: Configuration**
- [ ] Select primary genres
- [ ] Enter target audience
- [ ] Set languages, price point, books per year
- [ ] Choose brand colors
- [ ] Select brand values
- [ ] Click "Next" - should create PublishingFocus object

**Step 4: Review & Create**
- [ ] Review all entered information
- [ ] Click "Create Imprint" - should call `ImprintCreationService.create_from_wizard()`
- [ ] Verify imprint is created and saved
- [ ] Check wizard resets to step 1

**Key Testing Points**:
- Each step builds domain objects incrementally
- Validation at domain level (try entering invalid data)
- Session state holds domain objects, not dictionaries
- Service handles all persistence

#### Tab 2: 🤖 AI One-Shot Generation
- [ ] Enter imprint description
- [ ] Select model (Gemini/Claude/GPT)
- [ ] Adjust temperature slider
- [ ] Upload partial config (optional)
- [ ] Click "Generate Imprint" - should call `ImprintCreationService.create_from_ai()`
- [ ] View generated imprint
- [ ] Click "Edit in Wizard" - should populate wizard with generated data
- [ ] Click "Activate Imprint" - should change status to ACTIVE

**Key Testing Points**:
- AI generation creates complete Imprint object
- Can load generated imprint into wizard
- Can activate imprint after generation

---

## 🔍 Architecture Verification

### Check Domain Objects Are Used

Open browser console and check Streamlit session state:
- Should see `Imprint`, `Tournament`, `PublisherPersona` objects
- Should NOT see raw dictionaries for core data

### Check Service Layer

All operations should go through services:
- `ImprintCreationService` for imprint creation
- `TournamentService` for tournament operations
- No direct repository access from UI

### Check Repository Pattern

Data persistence should be handled by repositories:
- `ImprintRepository` for imprints (saves to `configs/imprints/*.json`)
- `TournamentRepository` for tournaments (saves to `tournaments/*.json`)

---

## 🐛 Known Issues to Watch For

### Potential Issues

1. **Import Errors**: If you see ModuleNotFoundError, check PYTHONPATH is set correctly
2. **Authentication**: Pages expect shared auth system at `/Users/fred/my-apps/shared/auth`
3. **LLM Calls**: AI generation requires valid API keys in `.env`
4. **File Paths**: Repositories expect standard directory structure

### Expected Behavior vs Old Version

| Feature | Old (Procedural) | New (OO) |
|---------|------------------|----------|
| Tournament data | Dict[str, Any] | Tournament object |
| Imprint data | Dict[str, Any] | Imprint object |
| Validation | UI level | Domain level |
| Data access | Direct file I/O | Repository pattern |
| Business logic | In UI functions | In services |

---

## 📊 Success Criteria

The refactored pages are successful if:

- [x] ✅ Pages load without errors
- [ ] All UI features work as before
- [ ] Domain objects are used instead of dictionaries
- [ ] Services handle all business logic
- [ ] Repositories handle all persistence
- [ ] Type errors caught by IDE (not runtime)
- [ ] Validation happens at domain level
- [ ] No direct file I/O in UI code

---

## 🔄 Comparison Testing

### Side-by-Side Comparison

To compare with original pages, you can run them in the main worktree:

```bash
# Original Tournament page (main worktree)
cd /Users/fred/xcu_my_apps/nimble/codexes-factory
PYTHONPATH="${PWD}/src:${PYTHONPATH}" uv run streamlit run src/codexes/pages/21_Imprint_Ideas_Tournament.py --server.port 8506

# Original Enhanced Creator (main worktree)
PYTHONPATH="${PWD}/src:${PYTHONPATH}" uv run streamlit run src/codexes/pages/20_Enhanced_Imprint_Creator.py --server.port 8507
```

Then compare:
- Port 8503 vs 8506 (Tournament)
- Port 8505 vs 8507 (Enhanced Creator)

---

## 📝 Feedback

When testing, please note:

1. **What works well**: Features that work correctly with new architecture
2. **What's broken**: Any errors or unexpected behavior
3. **What's missing**: Features that existed before but are missing
4. **Performance**: Is it faster/slower than original?
5. **UX differences**: Any changes to user experience

---

## 🛑 Stopping the Test Servers

When done testing:

```bash
# Find and kill the Streamlit processes
lsof -ti:8503,8505 | xargs kill
```

Or stop them individually:
```bash
kill $(lsof -ti:8503)  # Tournament
kill $(lsof -ti:8505)  # Enhanced Creator
```

---

## 📚 Next Steps After Testing

1. Fix any bugs found during testing
2. Migrate remaining pages (15, 18, 9)
3. Write unit tests for domain models
4. Write integration tests for services
5. Update documentation
6. Merge into main branch

---

**Happy Testing! 🎉**

The new architecture should provide better type safety, easier testing, and cleaner code organization.
