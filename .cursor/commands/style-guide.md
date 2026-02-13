
# Style Guidelines

## NixOS/Home-Manager Style

- Use 2-space indentation in all files
- Format Nix files with `nixfmt`
- Follow functional programming patterns
- Group related settings in modules
- Use descriptive names for options
- Document non-obvious settings with comments
- When creating new files for Nix flakes, ensure they are tracked by git before testing with nix commands
  - Untracked files can cause errors like "path '/nix/store/hash-source/path/to/file' does not exist"
  - Solution: Track files without staging using `git add --intent-to-add path/to/file` or `git add -N path/to/file`

## Neovim Style

- Use Lua for all configuration
- 2-space indentation, no tabs
- Leader key is `;`
- Format with proper whitespace and bracing style
- Wrap related plugin configs in feature-based groups
- Prefer native LSP functions over plugin equivalents

## Git Workflow

- Create focused, atomic commits
- Use `hub` as git wrapper
- Use `lazygit` for interactive Git operations
- Prefer rebase over merge for linear history
- Do not include co-authored by Claude information in commits
- Git config location: `~/.config/git/config`
- Credential storage: git-credential-manager with GPG backend
  - Initialize pass: `pass init YOUR_GPG_KEY_ID`
  - Credentials stored securely with GPG encryption

## 何時更新這份 Skill

| 情境 | 更新什麼 |
|------|----------|
| 切換 formatter 或 linter（如 nixfmt → alejandra） | 對應語言章節 |
| Neovim 更換核心 plugin 或 leader key | Neovim Style |
| 新增語言到常用工具鏈 | 新增對應章節 |
| Git 工具切換（如 hub → gh） | Git Workflow |
