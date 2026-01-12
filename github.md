# Windows 本地文件夹上传到 GitHub 全流程指南

本文档整理了一套**从 Windows 本地文件夹开始，到成功推送到 GitHub 仓库**的完整、可复用流程。适合初次配置，也适合以后换电脑、换项目直接照做。

---

## 一、前置条件

* Windows 系统
* 已注册 GitHub 账号
* 已安装 **Git for Windows**
* 使用 **PowerShell** 操作

> 说明：以下流程以 **SSH 方式推送 GitHub** 为主，这是长期使用最稳定、最省事的方式。

---

## 二、Git 基本身份配置（仅需一次）

在 PowerShell 中执行（任意目录均可）：

```powershell
git config --global user.name "zhimingliang"
git config --global user.email "zhimingliang897@gmail.com"
```

验证是否生效：

```powershell
git config --global --list
```

---

## 三、本地文件夹初始化为 Git 仓库

### 1. 进入你的项目目录

```powershell
cd E:\Code
```

> 请替换为你自己的真实文件夹路径。

### 2. 初始化 Git 仓库

```powershell
git init
```

### 3. 添加文件并进行第一次提交

```powershell
git add .
git commit -m "initial commit"
```

⚠️ 注意：

* **必须成功 commit**，否则后续推送会报：

  ```
  src refspec main does not match any
  ```

---

## 四、在 GitHub 上创建远程仓库

1. 登录 GitHub
2. New repository
3. 填写仓库名（如 `Code`）
4. **不要勾选** README / .gitignore / License
5. 创建完成后，复制仓库地址，例如：

```
git@github.com:lzm-bryan/Code.git
```

---

## 五、配置 SSH（仅需一次）

### 1. 生成 SSH Key

```powershell
ssh-keygen -t ed25519 -C "zhimingliang897@gmail.com"
```

一路回车即可，默认生成到：

```
C:\Users\<用户名>\.ssh\id_ed25519
```

---

### 2. 启用 ssh-agent（需要管理员权限）

**以管理员身份**打开 PowerShell，然后执行：

```powershell
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519
```

---

### 3. 将公钥添加到 GitHub

复制公钥：

```powershell
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | Set-Clipboard
```

GitHub → Settings → SSH and GPG keys → New SSH key

* Title：随意（如 `Windows-PC`）
* Key：粘贴刚复制的内容

---

### 4. 测试 SSH 连接

```powershell
ssh -T git@github.com
```

如果看到：

```text
Hi <username>! You've successfully authenticated...
```

说明 SSH 配置成功。

---

## 六、绑定远程仓库并推送代码

### 1. 设置主分支并添加远程仓库

```powershell
git branch -M main
git remote add origin git@github.com:lzm-bryan/Code.git
```

### 2. 推送到 GitHub

```powershell
git push -u origin main
```

至此，本地文件夹已成功上传到 GitHub。

---

## 七、后续日常更新流程（最常用）

以后每次改完代码，只需要：

```powershell
git add .
git commit -m "update"
git push
```

---

## 八、常见问题速查

### 1. `git` 无法识别

* Git 未安装或未加入 PATH
* 重新安装 Git for Windows

### 2. `src refspec main does not match any`

* 尚未进行 commit

```powershell
git commit -m "initial commit"
```

### 3. `Permission denied (publickey)`

* SSH key 未添加到 GitHub
* ssh-agent 未启动

---

## 九、总结

通过以上流程，你已经完成：

* Windows 下 Git 的标准配置
* SSH 安全连接 GitHub
* 本地项目到远程仓库的完整闭环

这套流程适用于 **Python / Jupyter / 普通代码项目**，可以长期复用。
