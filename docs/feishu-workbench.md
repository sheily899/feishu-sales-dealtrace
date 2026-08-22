# 飞书群聊销售分析工作台

该工作台将飞书测试群中的客户与销售文本消息整理为标准销售对话，交给
GTMSI 分析引擎，并在本地 Web 页面展示带原文证据的分析报告。

## 启动真实飞书测试群模式

1. 安装依赖：

   ```bash
   pip install -e ".[llm,feishu]"
   ```

2. 仅在本地 `.env` 中配置应用凭证与身份映射；不要提交该文件：

   ```env
   FEISHU_APP_ID=cli_xxx
   FEISHU_APP_SECRET=...
   FEISHU_ROLE_MAP={"ou_customer":"customer","ou_sales":"sales"}
   FEISHU_GROUP_ALLOWLIST=oc_test_group
   ```

3. 启动工作台：

   ```bash
   python -m gtmsi workbench --feishu --port 8766
   ```

打开 `http://127.0.0.1:8766`。页面每 3 秒同步一次本地状态；群内新消息到达后会显示为“客户”或“销售”，而不会展示飞书 Open ID。

## 本地持久化与隐私边界

真实飞书模式把消息适配字段和每个群的**最近一次**分析报告保存到：

```text
data/workbench.sqlite3
```

该目录已被 `.gitignore` 排除，不能提交到 GitHub。工作台重启时会按
`FEISHU_GROUP_ALLOWLIST` 中唯一的群 ID 恢复消息和最新报告；新消息到达后，
旧报告会自动失效，需再次点击“生成分析”。

这是单机面试演示存储，不提供加密、账号权限、多租户或云端备份。删除
`data/workbench.sqlite3` 即可清除本机持久化的群聊和报告。
