# WebNC User Guide

This guide provides comprehensive instructions for using WebNC, a local-first, keyboard-driven, two-panel file manager for Windows.

## Getting Started

### Installation
1. Ensure Python 3.9+ is installed and accessible via the `py` launcher
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   pip install cryptography   # for RSA-4096 certificate generation
   ```

### First Launch
1. Start the server:
   ```powershell
   py webnc_server.py
   ```
   Or use the management scripts:
   ```powershell
   .\run.bat              # start with HTTPS (default)
   .\run.bat --insecure    # start with HTTP (debug only)
   ```

2. Open your browser and navigate to `https://localhost:8000`
3. Accept the self-signed certificate warning (click "Advanced" → "Proceed to localhost")
4. Copy the session token from the server console output
5. Paste the token when prompted, or append it to the URL as `#token=<TOKEN>`

## User Interface Overview

WebNC features a classic two-panel layout inspired by Norton Commander:

```
+-------------------------------------------------------------+
| Menu Bar: Left | Files | Commands | Options | Right |       |
+-------------------------------------------------------------+
| Left Panel                                         Right Panel |
| (Path: /C/Users/)                                  (Path: /D/)   |
|                                                    |            |
| [Directory Listing]                                [Directory Listing] |
|                                                    |            |
|--------------------------------------------------|------------|
| Command Line: >                                  |            |
|                                                  |            |
| Status Bar: [Disk Info] [Alt+F1/F2: Drive Switch] |            |
+-------------------------------------------------------------+
| Fn Bar: F1-Help F3-View F4-Info F5-Copy F6-Move F7-MkDir F8-Del |
+-------------------------------------------------------------+
```

### Panels
- **Two Independent Panels**: Each panel shows a directory listing and maintains its own navigation state
- **Active Panel**: The panel with focus receives keyboard input (indicated by highlighted border)
- **Tab Key**: Switches active panel between left and right
- **Panel Operations**: Most file operations (copy, move, delete) work from active → opposite panel

### Menu Bar
- **Left**: View modes, sort options, drive switching, panel on/off
- **Files**: File operations (F3-F8), batch operations
- **Commands**: Advanced functions (Find File, Synchronize Directories, System Information, etc.)
- **Options**: UI configuration (default view, sort, hidden files, confirmations)
- **Right**: Mirrors Left menu for the right panel

### Fn Bar (Bottom)
- **F1**: Show help dialog (complete keyboard reference)
- **F3**: View file content (text files <64KB)
- **F4**: Show file/directory information (or edit if file)
- **F5**: Copy selected item(s) to opposite panel
- **F6**: Move/Rename selected item(s) to opposite panel
- **F7**: Create new directory
- **F8**: Delete selected item(s) (with confirmation)
- **F9**: Open file search dialog (populates opposite panel with results)
- **F10**: Show quit confirmation dialog
- **F11**: Toggle fullscreen mode (EGA Lines)

### Command Line
- Located at bottom center
- Accessible via clicking on the command input area
- Type command and press Enter to execute via `POST /api/exec`
- Command output appears in scrollable terminal area below panels
- Command history maintained (up/down arrows planned)
- When both panels hidden (Ctrl+O), terminal fills the full space

### Active Target
- `activeTarget` state controls which area receives keyboard input: `"panels"` or `"terminal"`
- Tab cycles: left panel → right panel → terminal → left panel
- Ctrl+O hides panels → auto-switches to terminal; shows panels → switches back
- Click on panels area → switches to panels; click on terminal area → switches to terminal
- Visual indicator: terminal border turns cyan when active

### Status Bar
- Shows current disk usage for active panel's drive
- Displays hints for drive switching (Alt+F1/F2)
- Shows current paths for both panels

## Keyboard Shortcuts

### Navigation
| Shortcut | Action |
|----------|--------|
| ↑ / ↓ | Move cursor up/down |
| Home / End | Move to first/last item |
| PgUp / PgDn | Page up/down |
| Enter | Open directory or launch file |
| Tab | Switch active panel (left → right → terminal → left) |
| Alt+F1 | Focus left panel drive selector |
| Alt+F2 | Focus right panel drive selector |

### Selection
| Shortcut | Action |
|----------|--------|
| Insert | Toggle selection of item under cursor |
| + | Select group (prompt for pattern) |
| - | Deselect group (prompt for pattern) |
| * | Invert selection (toggle all non-parent items) |

### File Operations
| Shortcut | Action |
|----------|--------|
| F3 | View file content |
| F4 | Show info (directory) / Edit (file) |
| F5 | Copy to opposite panel |
| F6 | Move to opposite panel / Rename |
| F7 | Create directory |
| F8 | Delete (with confirmation) |
| F9 | Search files |
| F10 | Quit application |

### Panel & View Controls
| Shortcut | Action |
|----------|--------|
| F1 | Show help |
| F2 | Toggle left menu |
| F11 | Toggle fullscreen mode |
| Ctrl+O | Toggle panels visibility (menu always works) |
| Ctrl+R | Refresh current panel (via menu) |
| Ctrl+U | Swap panels (via menu) |

### Dialog Navigation
| Shortcut | Action |
|----------|--------|
| Tab | Navigate between interactive elements |
| ↑ / ↓ | Navigate lists (where applicable) |
| Enter | Activate focused button or open selected item |
| Escape | Close dialog or cancel operation |

## Using the Interface

### Basic File Operations

#### Opening Directories
- Navigate with arrow keys and press Enter
- Or type a path in the command line (planned)
- Use drive switching (Alt+F1/F2) to jump to drive roots

#### Selecting Items
- Press Insert to toggle selection of current item
- Use + to select multiple items matching a pattern (e.g., `*.txt`)
- Use - to deselect items matching a pattern
- Use * to invert selection (select all unselected, deselect all selected)

#### Copying/Moving Files
1. Select source items in active panel
2. Ensure opposite panel shows target directory
3. Press F5 to copy or F6 to move
4. Monitor progress in operation status area (if async)
5. Verify results in opposite panel

#### Renaming Items
1. Select item to rename
2. Press F6
3. In the destination prompt, edit the name portion
4. Press Enter to confirm

#### Creating Directories
1. Navigate to parent directory
2. Press F7
3. Enter directory name
4. Press Enter to confirm

#### Deleting Items
1. Select items to delete
2. Press F8
3. Confirm deletion in dialog
4. Monitor progress (if async)

#### Uploading Files
1. Navigate to target directory in active panel
2. Use Commands menu or drag-and-drop (planned)
3. Select file to upload (max 100 MB)
4. File appears in active panel after upload

#### Downloading Files
1. Select file to download
2. Use Commands menu → Download
3. Browser downloads file with original filename

### Advanced Features

#### View Modes
Each panel can independently display content in different modes:
- **Brief**: Multi-column filename list (fastest for many files)
- **Full**: Detailed table with name, extension, time, size
- **Quick**: Preview of opposite panel's selection (content for files <64KB)
- **Info**: Directory summary + disk usage (shows info about opposite panel)
- **Tree**: Expandable directory tree (left/right navigation follows cursor)
- **Search**: Search results mode (activated via F9)

Change view mode via:
- Left/Right menu → View Modes
- Keyboard shortcuts (planned)

#### Sorting
Sort panel contents by:
- Name (alphabetical)
- Extension (file type)
- Time (modification date)
- Size (file size)
- Unsorted (filesystem order)

Click column headers in Full view or use Left/Right menu → Sort Options.

#### Filtering
Show only items matching a pattern:
1. Files menu → Filter...
2. Enter FNMatch pattern (e.g., `*.txt`, `*report*`)
3. Press Enter
4. Filter indicator `[pattern]` appears in path bar
5. Filter persists across navigation until cleared

To clear filter: Files menu → Filter... → clear input → Enter

#### Selection Groups
Work with sets of files using patterns:
- **Select Group (+)**: Adds matching items to current selection
- **Deselect Group (−)**: Removes matching items from current selection
- **Invert Selection (*)**: Toggles selection state of all non-parent items

Examples:
- `+ *.txt` selects all text files
- `- temp*` removes items starting with "temp"
- `*` inverts selection (useful for selecting all except a few)

#### Search (F9)
Find files across drives:
1. Press F9 to open search dialog
2. Enter search pattern (glob or regex)
3. Choose search type (glob/regex)
4. Set maximum results (default 200)
5. Press Enter to search
6. Results appear in opposite panel in Search view mode
7. Navigate results with ↑↓, press Enter to open directory
8. Press Escape to close search dialog and return to previous view

Search supports:
- Glob patterns: `*.txt`, `doc?.pdf`
- Regex patterns: `^report.*\.docx$`
- Case-sensitive matching

#### Directory Comparison
Compare two directories:
1. Set active panel to left directory, opposite to right directory
2. Commands menu → Compare Directories
3. Wait for async operation to complete
4. View results in four tabs:
   - Different: items that exist in both but differ
   - Only Left: items only in left directory
   - Only Right: items only in right directory
   - Same: identical items in both
5. Click any row to navigate to that location in the respective panel
6. Use show-filter toggles (→ = ≠ ←) to filter results by action type

#### Directory Synchronization
Synchronize directories (Total Commander style):
1. Commands menu → Synchronize Directories
2. Setup phase:
   - Set left and right paths
   - Enter filter pattern (optional)
   - Check options:
     - Subdirs: include subdirectories
     - By content: compare file content (slower but accurate)
     - Ignore date: ignore modification timestamps
     - Asymmetric: allow delete operations
   - Press [Compare] button
3. Results phase:
   - View file list with suggested actions (auto-marked based on options)
   - Show-filter toggles: → = ≠ ← (independent)
   - Per-row action cycling: click to cycle through available actions
   - Info bar: counts (Total, Same, Diff, L-only, R-only)
   - Bottom buttons: Re-compare, Mark All, Synchronize, Close
4. To customize actions:
   - Click rows to change action (null → copy_left_to_right → copy_right_to_left → null)
   - For asymmetric only_right items: null ↔ delete_right
   - Mark All: selects all suggested actions
   - Re-compare: repeats comparison with current settings
5. Press [Synchronize] to execute selected actions
6. Monitor progress in operation status area

#### Archive Browsing
View contents of archive files:
1. Navigate to archive file (.zip, .tar, .gz, .bz2, .xz)
2. Press F4 (or Enter) to view
3. ArchiveDialog shows contents in table:
   - Name, Size, Packed Size, Modified Date
4. For password-protected archives:
   - First attempt opens without password
   - On failure, prompts for password
   - Correct password caches for session
5. Navigate with ↑↓, press Enter to open parent directory
6. Escape closes dialog

*Note: Currently listing only; extraction/planned for future*

#### File Viewing and Editing
- **View (F3)**: Text files under 64KB shown in read-only viewer
- **Info (F4 on directory)**: Shows directory statistics and contents
- **Edit (F4 on file)**: Opens EditorDialog for text files < `max_edit_size` (default 1 MB, configurable via `editor.max_edit_size` in config.json)
  - Edit content in textarea
  - Ctrl+S indicates save shortcut
  - Save/Cancel buttons
  - Dirty tracking warns of unsaved changes
  - Size limit enforced for performance

#### System Information
Access via:
- Commands menu → System Information
- Shows: OS, hostname, CPU, RAM, uptime, drive table
- Refresh button for updated information
- Copy-to-clipboard planned

#### Navigation History
Each panel maintains history of visited directories:
- Commands menu → History
- Shows last 50 unique paths per panel
- ↑↓ navigation, Enter to navigate
- Clear history button
- Persists until cleared or browser data cleared

#### Configuration
Two configuration dialogs:

**Options → Configuration...** (UI Preferences):
- Default view mode (Brief/Full/Quick/Info/Tree)
- Default sort field/direction
- Show hidden files (global setting)
- Confirm delete/overwrite prompts
- Font size (px-based)
- Saved to browser localStorage

**Commands → Timeouts...** (Operation Settings):
- Per-operation retry count (0-10)
- Per-operation timeout (seconds)
- Per-operation polling interval (milliseconds)
- Affects: copy, move, batch-delete, search, compare, sync-plan, sync-execute, archive-list
- Saved to server config.json under `operations` key via PUT /api/config
- Changes apply immediately without restart

**Commands → Keybindings...** (Key Configuration):
- Customizable keyboard shortcuts for all actions
- Saved to server config.json under `keybindings` key

**Commands → Exec Rules...** (Command Execution Rules):
- Allowed/denied command prefixes for `/api/exec`
- Saved to server config.json under `exec` key

**Commands → Editor Limits...** (Editor Settings):
- Maximum file size for in-browser editing
- Saved to server config.json under `editor` key

#### Fullscreen Mode
Toggle with F11:
- Hides browser UI for maximal screen usage
- Press F11 again or Escape to exit
- Menu bar remains accessible via Alt key combinations
- Particularly useful for presentation or kiosk modes

#### Help System
Access via F1:
- Complete keyboard reference organized by category
- Navigation, Function Keys, Selection, Panels, View Modes, Commands, Sort, File Operations, Tips
- Dismiss via Escape, Enter, or F1
- Updated dynamically to reflect current configuration

## Settings Persistence

### Browser Settings (localStorage)
Stored in `nc_config` key:
- UI preferences (view mode, sort, hidden files, confirmations, font size)
- Shared across tabs for same origin
- Cleared when browser data cleared
- Modifiable via Options → Configuration... dialog

### Server Settings (config.json)
Stored in `config/config.json`:
- Operation timeout/retry settings for all 8 operation types (under `operations` key)
- Keyboard shortcuts (under `keybindings` key)
- Command execution rules (under `exec` key)
- Editor size limits (under `editor` key)
- Modified via Commands → Timeouts... dialog or PUT /api/config API
- Thread-safe atomic updates
- Survives server restarts
- Backed up automatically via .tmp + replace

### Session Data
- Authentication token: stored in sessionStorage (cleared on tab close)
- Operation polling state: temporary
- UI state: mixed (some in React state, some in localStorage)

## Tips and Best Practices

### Efficient Navigation
- Use Tab to switch panels rather than mouse
- Use drive switching (Alt+F1/F2) for quick root access
- Use Brief view mode for rapid scanning of many files
- Use sorting to group similar files (e.g., by extension)
- Use filtering to focus on specific file types

### File Operations
- Always verify source and destination before copy/move
- Use selection groups (+, −, *) for bulk operations
- Monitor long-running operations via status area
- Remember delete operations send items to permanent deletion (no recycle bin)
- Use rename (F6) for both moving and renaming within same directory

### Search and Comparison
- Use glob patterns (`*.txt`) for simple searches, regex for complex
- Limit search results to avoid excessive memory usage
- Use "By content" option in comparison/sync only when necessary (slower)
- Clear filters when no longer needed to avoid confusion

### Configuration
- Adjust timeouts based on your hardware and typical file sizes
- Lower retry counts for unstable storage (network drives)
- Enable hidden files only when needed (slight performance impact)
- Set confirmations based on your risk tolerance

### Security
- Remember this tool has full filesystem access with no sandbox
- Do not expose to untrusted networks without additional controls
- The self-signed certificate is acceptable for local use
- For production deployment, consider using a certificate from internal CA
- Authentication token is ephemeral and changes on each server start

### Performance
- Close unused browser tabs to conserve resources
- Large directories (>10K files) perform better in Brief view mode
- Archive listing performance depends on archive size and compression
- Sync operations benefit from SSD storage
- Consider excluding antivirus scanning of WebNC directories if needed

## Accessibility

### Keyboard Navigation
- All major functions accessible via keyboard
- Logical tab order in dialogs
- Clear focus indicators
- Escape consistently closes dialogs
- Enter activates default actions

### Visual Design
- High contrast color scheme (cyan/yellow on blue background)
- Semantic HTML elements for screen readers
- Scalable font sizes via configuration
- Minimal reliance on color alone for information
- Consistent spacing and layout

### Screen Reader Support
- ARIA labels planned for future improvement
- Semantic table usage for file listings
- Dialogs follow accessibility patterns
- Live regions planned for operation status updates

## Customization and Extensions

### UI Customization
- Modify `client/css/nc.css` for theme changes
- Adjust color schemes, fonts, spacing
- Add custom CSS classes as needed
- Changes require hard refresh (Ctrl+F5) to bypass cache

### Future Extension Points
WebNC is designed for extensibility:
1. **Authentication Providers**: Implement `AuthProvider` interface for AD/LDAP/JWT
2. **Virtual File System**: Extend `webnc/vfs/` for SFTP/FTP/cloud storage
3. **Operations**: Subclass `AbstractOperation` for new background tasks
4. **Frontend Components**: Add new dialogs or view modes in React
5. **Menu Items**: Extend menu system in `app.js`
6. **Configuration**: Add new operation types to `ConfigManager.OPERATION_DEFAULTS`

For detailed extension guidelines, see `docs/CODEBASE_DOCUMENTATION.md`.

## Troubleshooting Common Issues

### Startup Problems
- **"Address already in use"**: Kill existing process on port 8000
- **Blank page**: Check browser console for errors, hard refresh (Ctrl+F5)
- **Authentication fails**: Copy new token from server console after restart
- **Certificate warning**: Expected for self-signed cert; click "Proceed anyway"

### Operation Issues
- **Operation hangs**: Check server logs for errors, use `run.bat monitor` for auto-restart
- **Permission errors**: Run as administrator if accessing protected directories
- **Slow performance**: Check disk type (SSD vs HDD), close other applications
- **False negatives in search**: Verify pattern syntax, check case sensitivity

### Configuration Problems
- **Settings not saved**: Check browser localStorage permissions (private browsing?)
- **Operation timeouts not working**: Verify changed via PUT /api/config endpoint
- **UI settings reset**: Clear browser cache or check for conflicting extensions

For more detailed troubleshooting, see `docs/TROUBLESHOOTING.md`.

## Safety and Security Notices

> ⚠️ **Important Security Notice**: This tool has full filesystem access with no sandbox. All three protection levels (TLS, session auth, provider interface) are enabled by default for localhost. Do not expose to untrusted networks without additional controls.

### Data Safety
- Delete operations are permanent (no recycle bin)
- Overwrite warnings can be enabled in Configuration dialog
- Always verify targets before copy/move operations
- Consider testing on non-critical data first

### Network Safety
- Default binding to `127.0.0.1` (localhost only)
- `--host 0.0.0.0` exposes to all network interfaces (use only in trusted networks)
- TLS 1.3 encryption enabled by default
- Session tokens are ephemeral and never transmitted
- Replay protection and timestamp validation prevent session hijacking

### Compliance
- No persistent logs of file operations (planned audit log feature)
- Configuration changes logged at INFO level
- Authentication events logged (success/failure)
- Error conditions logged with appropriate detail
- See `docs/COMPLIANCE.md` for details

## Getting Help

### Documentation
- This guide: `docs/USER_GUIDE.md`
- API reference: `docs/API_REFERENCE.md`
- Architecture: `docs/ARCHITECTURE.md`
- Codebase: `docs/CODEBASE_DOCUMENTATION.md`
- Repository map: `docs/REPOSITORY_MAP.md`
- CLI tools: `docs/CLI-TOOLS.md`
- Compliance: `docs/COMPLIANCE.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- Development history: `History.md`

### Community
- GitHub Issues: https://github.com/anomalyco/opencode/issues
- Discussions: [Link if available]

### Support
For issues with the WebNC application itself:
1. Check `History.md` for similar resolved problems
2. Review `docs/TROUBLESHOOTING.md` for known issues
3. Examine server logs in `logs\nc_server.log`
4. Check browser console for frontend errors
5. Reproduce issue with steps to reproduce
6. Submit detailed issue report

Remember to include:
- WebNC version (from README or server startup)
- Operating system and version
- Browser and version
- Steps to reproduce
- Expected vs actual behavior
- Relevant log excerpts