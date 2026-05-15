# Boss 直聘训练爬虫

## 功能
- 采集 Boss 直聘北京、上海、深圳三城职位样本
- 默认职位词：`Python`、`数据分析`、`产品经理`
- 导出一个 Excel 单表
- 支持首次人工登录并保存会话，后续优先复用

## 项目结构
- `main.py`：命令行入口
- `config.py`：默认配置
- `models.py`：数据模型
- `browser.py`：Playwright 浏览器与会话
- `auth.py`：登录检测与状态保存
- `crawler.py`：搜索与分页采集
- `parser.py`：职位数据解析
- `exporter.py`：Excel 导出
- `utils.py`：日志、清洗、去重

## 安装依赖
```powershell
pip install -r requirements.txt
playwright install chromium
```

## 运行示例
```powershell
python main.py
python main.py --limit-per-city 5
python main.py --cities 北京 上海 --job-keywords Python 数据分析
python main.py --force-login
```

## 输出
- Excel：`output/boss_jobs.xlsx`
- 登录状态：`state/boss_storage_state.json`
- 日志：`logs/boss_scraper.log`

## 说明
- 若出现登录、滑块或安全校验，请在浏览器中手动完成。
- 第一版只做“列表页能拿就拿”的技能关键词，不进入详情页补抓。

