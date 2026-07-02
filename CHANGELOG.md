# Changelog

All notable changes to SoundVault will be documented in this file.

---

## [1.0.7] - 2026-07-02

### Fixed
- **Font size slider** now properly scales all UI text. Previously only inherited body text was affected; all hardcoded `font-size` values now use `calc(... * var(--font-scale))` for consistent scaling across the entire interface.
- **Glass blur** now controls all frosted glass elements. The modal, context menu, keyboard shortcut hint, and toast notifications all respond to the blur intensity slider instead of using fixed values.
- **Animation speed** now affects all transitions and animations across the UI (hover effects, card animations, toast animations, batch bar).
- **Background image** now properly applies opacity via a semi-transparent overlay, converts Windows backslashes to forward slashes for web compatibility, and persists when switching themes.

### Changed
- All backdrop-filter blur values now use `var(--blur)` instead of hardcoded pixel values.
- All transition and animation durations now use `calc(... * var(--anim-speed))` for consistent speed control.
- Theme switching (`setTheme`) now re-applies the current background style after changing themes.
- Appearance settings (font size, glass blur, glass opacity, animation speed, compact mode, background style/gradient/solid/image, opacity, accent) are now saved to the server config for persistence between sessions.
- Default config now includes all appearance settings with sensible defaults.

---

## [1.0.6] - 2026-07-02

### Changed
- Version bump for CI pipeline updates.

---

## [1.0.5] - 2026-xx-xx

### Added
- Auto-detect new audio files in the music folder.
- Tag-based organization with customizable colors.
- Episode tracking for grouping by project/scene.
- Star and use tracking to mark favorites and avoid repeats.
- Bulk operations for tagging, episode assignment, and deletion.
- Search and filter by title, artist, tags, notes, episodes, folders, and usage status.
- File browser and folder-based filtering.
- Import/Export database functionality.
- Built-in audio player with play, pause, seek, volume control, and mute.
- Drag & drop tracks into DAWs or file explorers.
- 12 built-in themes with live preview.
- Custom accent color picker.
- Font size slider (10px–18px).
- Animation speed control (0x–2x).
- Compact mode for denser content layout.
- Glass morphism UI with adjustable blur and opacity.
- Background customization: gradient presets, solid colors, custom images with opacity.
- One-click appearance reset.
- Keyboard shortcuts for all common actions.
- Cross-platform build support via PyInstaller and CI pipeline.
