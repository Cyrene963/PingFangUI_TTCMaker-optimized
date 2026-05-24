# PingFangUI_TTCMaker Optimized

这是 `PingFangUI_TTCMaker` 的低内存优化版，目标是解决原版在 iPad / a-Shell 上处理较大字体文件时容易崩溃的问题。

## 为什么原版容易崩

原版脚本的核心问题：
- 整体读入源字体
- 对每个子字体记录做 `copy.deepcopy`
- 最后再一次性把所有字体对象合并成一个 `TTCollection`

如果源字体本身有 20MB+，内存会被迅速放大，在 iPad 上很容易崩。

## 这个优化版做了什么

- 逐个子字体生成
- 每个子字体先落盘到临时目录
- 最后再从磁盘读取并合并成 TTC
- 提供 `--no-merge` 模式：只生成中间子字体，不做最终合并

## 文件

- `make_lowmem_pingfangui_ttc.py`：低内存生成脚本
- `names.json`：子字体 name 表模板
- `hywh.ttf`：示例字体

## 用法

### 正常模式

```bash
python3 make_lowmem_pingfangui_ttc.py 你的字体.ttf
```

默认会：
1. 生成中间子字体到 `pingfangui_parts/`
2. 合并成 `PingFangUI.ttc`
3. 删除中间文件

### 保命模式（推荐 iPad 先试这个）

```bash
python3 make_lowmem_pingfangui_ttc.py 你的字体.ttf --no-merge
```

这会：
- 只生成中间子字体
- 不做最终 TTC 合并
- 最终合并这一步最吃内存，所以 iPad 上先跑这个更稳

### 保留中间文件

```bash
python3 make_lowmem_pingfangui_ttc.py 你的字体.ttf --keep-temp
```

## 建议流程

### iPad / a-Shell 最稳流程

1. 先运行 `--no-merge`
2. 确认中间子字体都成功生成
3. 如果 iPad 内存还能扛，再尝试不带 `--no-merge` 合并
4. 如果合并仍吃力，就把中间文件拿到电脑上做最终合并

## 注意

这版只是解决“脚本内存爆炸”的问题。
如果你在 Lara / respring / 覆盖系统字体这一步仍闪退，那是设备侧或注入链路问题，不一定是 TTC 生成脚本本身的问题。
