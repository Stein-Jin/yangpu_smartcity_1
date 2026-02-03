# 事件分析系统 (Event Analysis System)

## 项目介绍

事件分析系统是一个基于 Flask 和 ECharts 开发的可视化分析工具，用于统计和展示指定时间段内的事件类型分布、小区事件排名以及事件发生趋势。

## 功能特性

### 1. 事件类型分析（饼图）
- 显示三类事件的数量和占比：
  - 杨浦楼道电弧漏电特别严重报警
  - 杨浦住宅楼道火灾烟雾连续报警
  - 杨浦非机动车库电弧漏电特别严重报警
- 饼图中心显示事件总数
- 图例清晰展示各事件类型的占比

### 2. 日期选择功能
- 下拉选择两个统计周期：
  - 2025年11月11日-12月10日
  - 2025年12月11日-2026年1月10日
- 实时更新所有图表数据

### 3. 事件统计信息
- 显示所选时间段的事件总数
- 展示排名前三的事件类型及其占比和数量
- 提供概括性文字描述，分析事件发生趋势

### 4. 小区事件排名（柱状图）
- 按小区统计指定事件类型的发生次数
- 支持按事件名称筛选（仅显示 I 级事件）
- 直观展示各小区的事件发生情况

### 5. 事件趋势分析（折线图）
- 按天统计事件发生次数
- 不同事件类型使用不同颜色区分
- 清晰展示事件发生的时间趋势

### 6. 事件详情表格
- 显示事件类型、优先级、发生次数和占比
- 限制只显示前 5 行数据
- 支持滚动查看

## 技术栈

- **后端**：Flask (Python)、Node.js (Express)
- **前端**：HTML5、CSS3、JavaScript、ECharts
- **数据库**：PostgreSQL

## 安装与运行

### 方法一：使用 Flask 后端（推荐）

1. **安装依赖**
   ```bash
   pip install flask psycopg2-binary
   ```

2. **配置数据库连接**
   - 编辑 `app.py` 文件中的 `db_config` 部分，设置正确的数据库连接信息

3. **启动服务**
   ```bash
   python app.py
   ```

4. **访问应用**
   - 浏览器打开：http://127.0.0.1:5000

### 方法二：使用 Node.js 后端

1. **安装依赖**
   ```bash
   npm install
   ```

2. **配置数据库连接**
   - 编辑 `server.js` 文件中的 `pool` 配置，设置正确的数据库连接信息

3. **启动服务**
   ```bash
   npm start
   ```

4. **访问应用**
   - 浏览器打开：http://localhost:3000

## 项目结构

```
event-analysis/
├── templates/
│   └── index.html          # 前端页面
├── app.py                  # Flask 后端应用
├── server.js               # Node.js 后端应用
├── package.json            # Node.js 依赖配置
├── .gitignore              # Git 忽略文件配置
└── README.md               # 项目说明文档
```

## 数据来源

数据来源于 PostgreSQL 数据库的两个模式：
- `brain_event_rule.event_record`：事件记录
- `brain_device_manage.sensor_cgqdw`：传感器信息

## 核心 API

### 1. 获取事件统计数据
- **接口**：`/api/events`
- **参数**：`period`（统计周期）
- **返回**：事件类型、优先级、数量和占比

### 2. 获取事件名称列表
- **接口**：`/api/event-names`
- **返回**：I 级事件名称列表

### 3. 获取事件趋势数据
- **接口**：`/api/event-trends`
- **参数**：`period`（统计周期）、`event_name`（事件名称，可选）
- **返回**：按天统计的事件发生数据

### 4. 获取事件趋势统计信息
- **接口**：`/api/event-trend-stats`
- **参数**：`period`（统计周期）、`event_name`（事件名称，可选）
- **返回**：事件发生的最大值、最小值、平均值和主要事件类型

### 5. 获取小区事件排名
- **接口**：`/api/community-events`
- **参数**：`period`（统计周期）、`event_name`（事件名称，可选）
- **返回**：按小区统计的事件发生数据

## 注意事项

1. 系统默认只统计 `project_code = '4'` 的数据
2. 事件优先级筛选为 `Ⅰ级`
3. 时间范围限制在 2025-11-11 至 2026-01-10
4. 仅统计指定的三类事件类型

## 截图示例

### 主页面
![主页面截图](https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=event%20analysis%20dashboard%20with%20pie%20chart%2C%20bar%20chart%20and%20line%20chart%2C%20showing%20event%20statistics&image_size=landscape_16_9)

## 许可证

ISC License

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！
