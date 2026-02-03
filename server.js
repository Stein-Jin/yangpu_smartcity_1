const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = 3000;

// 配置CORS
app.use(cors());

// 配置静态文件服务
app.use(express.static(__dirname));

// 数据库连接配置
const pool = new Pool({
    user: 'postgres', // 默认用户名，可根据实际情况修改
    host: '172.17.6.150',
    database: 'postgres', // 默认数据库名，可根据实际情况修改
    password: 'postgres', // 默认密码，可根据实际情况修改
    port: 5432,
});

// API接口：获取事件统计数据
app.get('/api/events', async (req, res) => {
    try {
        const { period } = req.query;
        
        // SQL查询语句
        const sql = `
            WITH period_event_detail AS (
                -- 第一步：统计各时间段-各事件类型的事件数
                SELECT
                    er.event_name,
                    CASE
                        WHEN er.gmt_create >= '2025-11-11' AND er.gmt_create < '2025-12-11' THEN '2025年11月11日-12月10日'
                        WHEN er.gmt_create >= '2025-12-11' AND er.gmt_create < '2026-01-11' THEN '2025年12月11日-2026年1月10日'
                        ELSE '其他时间段'
                    END AS time_period,
                    COUNT(1) AS event_count
                FROM
                    brain_event_rule.event_record er
                INNER JOIN brain_device_manage.sensor_cgqdw sc
                    ON er.sensor_id = sc.sensor_id
                    AND sc.project_code = '4'
                WHERE
                    er.gmt_create BETWEEN '2025-11-11' AND '2026-01-10 23:59:59'
                GROUP BY
                    er.event_name,
                    time_period
            ),
            period_total AS (
                -- 第二步：统计各时间段的总事件数
                SELECT
                    time_period,
                    SUM(event_count) AS total_count
                FROM
                    period_event_detail
                GROUP BY
                    time_period
            )
            -- 第三步：关联计算占比
            SELECT
                ped.event_name,
                ped.time_period,
                ped.event_count,
                -- 计算占比，保留2位小数，乘以100转为百分比格式
                ROUND((ped.event_count::NUMERIC / pt.total_count) * 100, 2) AS ratio_percent
            FROM
                period_event_detail ped
            INNER JOIN period_total pt
                ON ped.time_period = pt.time_period
            WHERE
                ped.time_period = $1
            -- 排序便于查看
            ORDER BY
                ratio_percent DESC;
        `;
        
        // 执行查询
        const result = await pool.query(sql, [period]);
        
        // 返回结果
        res.json(result.rows);
    } catch (error) {
        console.error('Error executing query:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// 根路径返回HTML文件
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// 启动服务器
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});