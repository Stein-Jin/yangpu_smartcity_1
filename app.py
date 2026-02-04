import psycopg2
from flask import Flask, jsonify, request, render_template
import json
import os

app = Flask(__name__)

# 数据库连接配置
db_config = {
    'host': '172.17.6.150',
    'database': 'brain_data',
    'user': 'readonly_jsj',
    'password': 'jsjDksz0121@#',
    'port': '5432',
}

def get_db_connection():
    conn = psycopg2.connect(**db_config)
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/topology')
def topology():
    return render_template('topology.html')

@app.route('/api/events')
def get_events():
    try:
        period = request.args.get('period')
        conn = get_db_connection()
        cur = conn.cursor()
        
        # SQL查询语句
        sql = """
            WITH period_event_detail AS (
                -- 第一步：统计各时间段-各指定事件类型的事件数
                SELECT
                    er.event_name,
                    er.priority,
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
                -- 核心筛选：仅保留指定的event_name
                WHERE
                    er.gmt_create BETWEEN '2025-11-11' AND '2026-01-10 23:59:59'
                    AND er.event_name IN (
                        '杨浦消防门常开告警',
                        '杨浦消防通道门30分钟常开预警',
                        '杨浦楼道堆物持续24小时预警',
                        '杨浦楼道堆物告警',
                        '杨浦住宅楼道火灾烟雾预警',
                        '杨浦消防通道门24小时常开警告',
                        '杨浦楼道堆物持续1周警告',
                        '杨浦楼道电弧漏电较重报警',
                        '杨浦楼道电弧漏电特别严重报警',
                        '杨浦楼道堆物持续1个月报警',
                        '杨浦消防通道门1周常开报警',
                        '杨浦非机动车库电弧漏电较重报警',
                        '杨浦住宅楼道火灾烟雾连续报警',
                        '杨浦非机动车库电弧漏电特别严重报警',
                        '杨浦非机动车库电弧漏电严重报警'
                    )
                GROUP BY
                    er.event_name,
                    er.priority,
                    time_period
            ),
            period_total AS (
                -- 第二步：统计各时间段内指定事件类型的总事件数
                SELECT
                    time_period,
                    SUM(event_count) AS total_count
                FROM
                    period_event_detail
                GROUP BY
                    time_period
            )
            -- 第三步：关联计算指定事件类型的占比
            SELECT
                ped.event_name,
                priority,
                ped.time_period,
                ped.event_count,
                -- 计算占比，保留2位小数，乘以100转为百分比格式
                ROUND((ped.event_count::NUMERIC / pt.total_count) * 100, 2) AS ratio_percent
            FROM
                period_event_detail ped
            INNER JOIN period_total pt
                ON ped.time_period = pt.time_period
            WHERE
                ped.time_period = %s
            -- 排序便于查看
            ORDER BY
                ratio_percent DESC;
        """
        
        cur.execute(sql, (period,))
        results = cur.fetchall()
        
        # 转换结果为JSON格式
        rows = []
        for row in results:
            rows.append({
                'event_name': row[0],
                'priority': row[1],
                'time_period': row[2],
                'event_count': row[3],
                'ratio_percent': row[4]
            })
        
        cur.close()
        conn.close()
        
        return jsonify(rows)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/event-names')
def get_event_names():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # SQL查询语句，只获取指定的三类事件名称
        sql = """
            SELECT DISTINCT
                er.event_name
            FROM
                brain_event_rule.event_record er
            INNER JOIN brain_device_manage.sensor_cgqdw sc
                ON er.sensor_id = sc.sensor_id
                AND sc.project_code = '4'
            WHERE
                er.priority = 'Ⅰ级'
                AND er.gmt_create BETWEEN '2025-11-11' AND '2026-01-10 23:59:59'
                AND er.event_name IN (
                    '杨浦楼道电弧漏电特别严重报警',
                    '杨浦住宅楼道火灾烟雾连续报警',
                    '杨浦非机动车库电弧漏电特别严重报警'
                )
            ORDER BY
                er.event_name;
        """
        cur.execute(sql)
        event_names = [row[0] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return jsonify(event_names)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/event-trend-stats')
def get_event_trend_stats():
    try:
        period = request.args.get('period')
        event_name = request.args.get('event_name')
        conn = get_db_connection()
        cur = conn.cursor()
        
        # SQL查询语句，获取按天统计的数据
        if event_name and event_name != 'all':
            sql = """
                SELECT
                    TO_CHAR(er.gmt_create, 'YYYY-MM-DD') AS event_date,
                    COUNT(1) AS total_event_count
                FROM
                    brain_event_rule.event_record er
                INNER JOIN brain_device_manage.sensor_cgqdw sc
                    ON er.sensor_id = sc.sensor_id
                    AND sc.project_code = '4'
                WHERE
                    er.priority = 'Ⅰ级'
                    AND er.gmt_create BETWEEN '2025-11-11' AND '2026-01-10 23:59:59'
                    AND er.event_name = %s
                    AND (
                        CASE
                            WHEN er.gmt_create >= '2025-11-11' AND er.gmt_create < '2025-12-11' THEN '2025年11月11日-12月10日'
                            WHEN er.gmt_create >= '2025-12-11' AND er.gmt_create < '2026-01-11' THEN '2025年12月11日-2026年1月10日'
                            ELSE '其他时间段'
                        END) = %s
                GROUP BY
                    event_date
                ORDER BY
                    event_date;
            """
            cur.execute(sql, (event_name, period))
        else:
            sql = """
                SELECT
                    TO_CHAR(er.gmt_create, 'YYYY-MM-DD') AS event_date,
                    COUNT(1) AS total_event_count
                FROM
                    brain_event_rule.event_record er
                INNER JOIN brain_device_manage.sensor_cgqdw sc
                    ON er.sensor_id = sc.sensor_id
                    AND sc.project_code = '4'
                WHERE
                    er.priority = 'Ⅰ级'
                    AND er.gmt_create BETWEEN '2025-11-11' AND '2026-01-10 23:59:59'
                    AND er.event_name IN (
                        '杨浦楼道电弧漏电特别严重报警',
                        '杨浦住宅楼道火灾烟雾连续报警',
                        '杨浦非机动车库电弧漏电特别严重报警'
                    )
                    AND (
                        CASE
                            WHEN er.gmt_create >= '2025-11-11' AND er.gmt_create < '2025-12-11' THEN '2025年11月11日-12月10日'
                            WHEN er.gmt_create >= '2025-12-11' AND er.gmt_create < '2026-01-11' THEN '2025年12月11日-2026年1月10日'
                            ELSE '其他时间段'
                        END) = %s
                GROUP BY
                    event_date
                ORDER BY
                    event_date;
            """
            cur.execute(sql, (period,))
        
        daily_counts = cur.fetchall()
        
        # 计算统计数据
        counts = [row[1] for row in daily_counts]
        max_count = max(counts) if counts else 0
        min_count = min(counts) if counts else 0
        avg_count = sum(counts) / len(counts) if counts else 0
        avg_count = round(avg_count, 2)
        
        # 获取主要波动原因（前3个波动较大的事件类型）
        if event_name and event_name != 'all':
            # 如果指定了事件名称，只返回该事件
            main_events = [event_name]
        else:
            # 否则，获取前3个事件类型
            sql = """
                SELECT
                    er.event_name,
                    COUNT(1) AS total_event_count
                FROM
                    brain_event_rule.event_record er
                INNER JOIN brain_device_manage.sensor_cgqdw sc
                    ON er.sensor_id = sc.sensor_id
                    AND sc.project_code = '4'
                WHERE
                    er.priority = 'Ⅰ级'
                    AND er.gmt_create BETWEEN '2025-11-11' AND '2026-01-10 23:59:59'
                    AND er.event_name IN (
                        '杨浦楼道电弧漏电特别严重报警',
                        '杨浦住宅楼道火灾烟雾连续报警',
                        '杨浦非机动车库电弧漏电特别严重报警'
                    )
                    AND (
                        CASE
                            WHEN er.gmt_create >= '2025-11-11' AND er.gmt_create < '2025-12-11' THEN '2025年11月11日-12月10日'
                            WHEN er.gmt_create >= '2025-12-11' AND er.gmt_create < '2026-01-11' THEN '2025年12月11日-2026年1月10日'
                            ELSE '其他时间段'
                        END) = %s
                GROUP BY
                    er.event_name
                ORDER BY
                    total_event_count DESC
                LIMIT 3;
            """
            cur.execute(sql, (period,))
            main_events_result = cur.fetchall()
            main_events = [row[0] for row in main_events_result]
        
        cur.close()
        conn.close()
        
        # 构建响应数据
        stats = {
            'period': period,
            'max_count': max_count,
            'min_count': min_count,
            'avg_count': avg_count,
            'main_events': main_events
        }
        
        return jsonify(stats)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/event-trends')
def get_event_trends():
    try:
        period = request.args.get('period')
        event_name = request.args.get('event_name')
        conn = get_db_connection()
        cur = conn.cursor()
        
        # SQL查询语句
        if event_name and event_name != 'all':
            sql = """
                SELECT
                    -- 统计周期
                    CASE
                        WHEN er.gmt_create >= '2025-11-11' AND er.gmt_create < '2025-12-11' THEN '2025年11月11日-12月10日'
                        WHEN er.gmt_create >= '2025-12-11' AND er.gmt_create < '2026-01-11' THEN '2025年12月11日-2026年1月10日'
                        ELSE '其他时间段'
                    END AS time_period,
                    -- 事件发生日期（核心分组维度，无小时）
                    TO_CHAR(er.gmt_create, 'YYYY-MM-DD') AS event_date,
                    -- 事件名称（明确当天发生的具体事件）
                    er.event_name,
                    -- 该日期该事件在周期内的总数量
                    COUNT(1) AS total_event_count
                FROM
                    brain_event_rule.event_record er
                INNER JOIN brain_device_manage.sensor_cgqdw sc
                    ON er.sensor_id = sc.sensor_id
                    AND sc.project_code = '4'
                WHERE
                    er.priority = 'Ⅰ级'  -- 筛选I级事件
                    AND er.gmt_create BETWEEN '2025-11-11' AND '2026-01-10 23:59:59'
                    AND er.event_name = %s
                    AND (
                        CASE
                            WHEN er.gmt_create >= '2025-11-11' AND er.gmt_create < '2025-12-11' THEN '2025年11月11日-12月10日'
                            WHEN er.gmt_create >= '2025-12-11' AND er.gmt_create < '2026-01-11' THEN '2025年12月11日-2026年1月10日'
                            ELSE '其他时间段'
                        END) = %s
                -- 仅按周期、日期、事件名称分组（核心：只保留日期维度，无小时/小区）
                GROUP BY
                    time_period,
                    event_date,
                    er.event_name
                -- 排序：周期→日期→事件名称，便于查看
                ORDER BY
                    time_period,
                    event_date,
                    er.event_name;
            """
            cur.execute(sql, (event_name, period))
        else:
            sql = """
                SELECT
                    -- 统计周期
                    CASE
                        WHEN er.gmt_create >= '2025-11-11' AND er.gmt_create < '2025-12-11' THEN '2025年11月11日-12月10日'
                        WHEN er.gmt_create >= '2025-12-11' AND er.gmt_create < '2026-01-11' THEN '2025年12月11日-2026年1月10日'
                        ELSE '其他时间段'
                    END AS time_period,
                    -- 事件发生日期（核心分组维度，无小时）
                    TO_CHAR(er.gmt_create, 'YYYY-MM-DD') AS event_date,
                    -- 事件名称（明确当天发生的具体事件）
                    er.event_name,
                    -- 该日期该事件在周期内的总数量
                    COUNT(1) AS total_event_count
                FROM
                    brain_event_rule.event_record er
                INNER JOIN brain_device_manage.sensor_cgqdw sc
                    ON er.sensor_id = sc.sensor_id
                    AND sc.project_code = '4'
                WHERE
                    er.priority = 'Ⅰ级'  -- 筛选I级事件
                    AND er.gmt_create BETWEEN '2025-11-11' AND '2026-01-10 23:59:59'
                    AND er.event_name IN (
                        '杨浦楼道电弧漏电特别严重报警',
                        '杨浦住宅楼道火灾烟雾连续报警',
                        '杨浦非机动车库电弧漏电特别严重报警'
                    )
                    AND (
                        CASE
                            WHEN er.gmt_create >= '2025-11-11' AND er.gmt_create < '2025-12-11' THEN '2025年11月11日-12月10日'
                            WHEN er.gmt_create >= '2025-12-11' AND er.gmt_create < '2026-01-11' THEN '2025年12月11日-2026年1月10日'
                            ELSE '其他时间段'
                        END) = %s
                -- 仅按周期、日期、事件名称分组（核心：只保留日期维度，无小时/小区）
                GROUP BY
                    time_period,
                    event_date,
                    er.event_name
                -- 排序：周期→日期→事件名称，便于查看
                ORDER BY
                    time_period,
                    event_date,
                    er.event_name;
            """
            cur.execute(sql, (period,))
        
        results = cur.fetchall()
        
        # 转换结果为JSON格式
        rows = []
        for row in results:
            rows.append({
                'time_period': row[0],
                'event_date': row[1],
                'event_name': row[2],
                'total_event_count': row[3]
            })
        
        cur.close()
        conn.close()
        
        return jsonify(rows)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/community-events')
def get_community_events():
    try:
        period = request.args.get('period')
        event_name = request.args.get('event_name')
        conn = get_db_connection()
        cur = conn.cursor()
        
        # SQL查询语句
        if event_name and event_name != 'all':
            sql = """
                SELECT
                    -- 统计周期
                    CASE
                        WHEN er.gmt_create >= '2025-11-11' AND er.gmt_create < '2025-12-11' THEN '2025年11月11日-12月10日'
                        WHEN er.gmt_create >= '2025-12-11' AND er.gmt_create < '2026-01-11' THEN '2025年12月11日-2026年1月10日'
                        ELSE '其他时间段'
                    END AS time_period,
                    -- 住宅小区名称（核心分组维度）
                    sc.community_name,
                    -- 事件名称（明确小区发生的具体事件）
                    er.event_name,
                    -- 该小区该事件在周期内的总数量
                    COUNT(1) AS total_event_count
                FROM
                    brain_event_rule.event_record er
                INNER JOIN brain_device_manage.sensor_cgqdw sc
                    ON er.sensor_id = sc.sensor_id
                    AND sc.project_code = '4'
                WHERE
                    er.priority = 'Ⅰ级'  
                    AND er.gmt_create BETWEEN '2025-11-11' AND '2026-01-10 23:59:59'
                    AND er.event_name = %s
                    AND (
                        CASE
                            WHEN er.gmt_create >= '2025-11-11' AND er.gmt_create < '2025-12-11' THEN '2025年11月11日-12月10日'
                            WHEN er.gmt_create >= '2025-12-11' AND er.gmt_create < '2026-01-11' THEN '2025年12月11日-2026年1月10日'
                            ELSE '其他时间段'
                        END) = %s
                -- 仅按周期、小区、事件名称分组（核心：只保留小区维度）
                GROUP BY
                    time_period,
                    sc.community_name,
                    er.event_name
                -- 排序：周期→小区→事件名称，便于查看
                ORDER BY
                    time_period,
                    total_event_count DESC,
                    sc.community_name,
                    er.event_name;
            """
            cur.execute(sql, (event_name, period))
        else:
            sql = """
                SELECT
                    -- 统计周期
                    CASE
                        WHEN er.gmt_create >= '2025-11-11' AND er.gmt_create < '2025-12-11' THEN '2025年11月11日-12月10日'
                        WHEN er.gmt_create >= '2025-12-11' AND er.gmt_create < '2026-01-11' THEN '2025年12月11日-2026年1月10日'
                        ELSE '其他时间段'
                    END AS time_period,
                    -- 住宅小区名称（核心分组维度）
                    sc.community_name,
                    -- 事件名称（明确小区发生的具体事件）
                    er.event_name,
                    -- 该小区该事件在周期内的总数量
                    COUNT(1) AS total_event_count
                FROM
                    brain_event_rule.event_record er
                INNER JOIN brain_device_manage.sensor_cgqdw sc
                    ON er.sensor_id = sc.sensor_id
                    AND sc.project_code = '4'
                WHERE
                    er.priority = 'Ⅰ级'  -- 筛选I级事件（值为'I'则改为'er.priority = 'I''）
                    AND er.gmt_create BETWEEN '2025-11-11' AND '2026-01-10 23:59:59'
                    AND er.event_name IN (
                        '杨浦楼道电弧漏电特别严重报警',
                        '杨浦住宅楼道火灾烟雾连续报警',
                        '杨浦非机动车库电弧漏电特别严重报警'
                    )
                    AND (
                        CASE
                            WHEN er.gmt_create >= '2025-11-11' AND er.gmt_create < '2025-12-11' THEN '2025年11月11日-12月10日'
                            WHEN er.gmt_create >= '2025-12-11' AND er.gmt_create < '2026-01-11' THEN '2025年12月11日-2026年1月10日'
                            ELSE '其他时间段'
                        END) = %s
                -- 仅按周期、小区、事件名称分组（核心：只保留小区维度）
                GROUP BY
                    time_period,
                    sc.community_name,
                    er.event_name
                -- 排序：周期→小区→事件名称，便于查看
                ORDER BY
                    time_period,
                    total_event_count DESC,
                    sc.community_name,
                    er.event_name;
            """
            cur.execute(sql, (period,))
        
        results = cur.fetchall()
        
        # 转换结果为JSON格式
        rows = []
        for row in results:
            rows.append({
                'time_period': row[0],
                'community_name': row[1],
                'event_name': row[2],
                'total_event_count': row[3]
            })
        
        cur.close()
        conn.close()
        
        return jsonify(rows)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/device-data')
def get_device_data():
    try:
        building_name = request.args.get('building_name')
        conn = get_db_connection()
        cur = conn.cursor()
        
        # SQL查询语句 - 根据原型文件中的查询逻辑
        sql = """
            SELECT 
               设备编号, 
               点位名称, 
               设备类别, 
               数值名称, 
               数值, 
               最后上报时间 
            FROM 
               (
                 -- 1. 水压监测数据 
                 SELECT 
                   sc.sensor_id AS 设备编号, 
                   sc.address AS 点位名称, 
                   sc.sensor_name AS 设备类别, 
                   wp."WaterPressure" AS 数值, 
                   '水压值' AS 数值名称, 
                   wp.received_time AS 最后上报时间, 
                   '水压监测' AS 数据类型, 
                   ROW_NUMBER() OVER (PARTITION BY sc.sensor_id ORDER BY wp.received_time DESC) AS row_num 
                 FROM 
                   brain_device_manage.data_log_water_pressure wp 
                   INNER JOIN sensor_cgqdw sc ON wp.device_id = sc.sensor_id 
                 WHERE 
                   sc.address LIKE %s 
                   AND sc.project_code = '4' 
                   AND wp.received_time >= '2026-01-20 23:59:59' UNION ALL 
                   -- 2. 环境监测-仅保留温度数据 
                 SELECT 
                   sc.sensor_id AS 设备编号, 
                   sc.address AS 点位名称, 
                   sc.sensor_name AS 设备类别, 
                   wp."Temperature" AS 数值, 
                   '温度' AS 数值名称, 
                   wp.received_time AS 最后上报时间, 
                   '环境监测' AS 数据类型, 
                   ROW_NUMBER() OVER (PARTITION BY sc.sensor_id ORDER BY wp.received_time DESC) AS row_num 
                 FROM 
                   brain_device_manage.data_log_environmental wp 
                   INNER JOIN sensor_cgqdw sc ON wp.device_id = sc.sensor_id 
                 WHERE 
                   sc.address LIKE %s 
                   AND sc.project_code = '4' 
                   AND wp.received_time >= '2026-01-20 23:59:59' UNION ALL 
                   -- 3. 液位监测数据（改为仅保留最新1条） 
                 SELECT 
                   sc.sensor_id AS 设备编号, 
                   sc.address AS 点位名称, 
                   sc.sensor_name AS 设备类别, 
                   wp."LiquidLevel" AS 数值, 
                   '液位' AS 数值名称, 
                   wp.received_time AS 最后上报时间, 
                   '液位监测' AS 数据类型, 
                   ROW_NUMBER() OVER (PARTITION BY sc.sensor_id ORDER BY wp.received_time DESC) AS row_num 
                 FROM 
                   brain_device_manage.data_log_liquid_level wp 
                   INNER JOIN sensor_cgqdw sc ON wp.device_id = sc.sensor_id 
                 WHERE 
                   sc.address LIKE %s 
                   AND sc.project_code = '4' 
                   AND wp.received_time >= '2026-01-20 23:59:59' UNION ALL 
                   -- 4. 电气火灾监测数据 
                 SELECT 
                   sc.sensor_id AS 设备编号, 
                   sc.address AS 点位名称, 
                   sc.sensor_name AS 设备类别, 
                   wp."VoltageC" AS 数值, 
                   '电压C' AS 数值名称, 
                   wp.received_time AS 最后上报时间, 
                   '电气火灾监测' AS 数据类型, 
                   ROW_NUMBER() OVER (PARTITION BY sc.sensor_id ORDER BY wp.received_time DESC) AS row_num 
                 FROM 
                   brain_device_manage.data_log_electrical_fire wp 
                   INNER JOIN sensor_cgqdw sc ON wp.device_id = sc.sensor_id 
                 WHERE 
                   sc.address LIKE %s 
                   AND sc.project_code = '4' 
                   AND wp.received_time >= '2026-01-20 23:59:59' UNION ALL 
                   -- 5. 消防柜控制数据 
                 SELECT 
                   sc.sensor_id AS 设备编号, 
                   sc.address AS 点位名称, 
                   sc.sensor_name AS 设备类别, 
                   wp."DevWorking01" AS 数值, 
                   '设备运行01' AS 数值名称, 
                   wp.received_time AS 最后上报时间, 
                   '消防柜控制' AS 数据类型, 
                   ROW_NUMBER() OVER (PARTITION BY sc.sensor_id ORDER BY wp.received_time DESC) AS row_num 
                 FROM 
                   brain_device_manage.data_log_file_control wp 
                   INNER JOIN sensor_cgqdw sc ON wp.device_id = sc.sensor_id 
                 WHERE 
                   sc.address LIKE %s 
                   AND sc.project_code = '4' 
                   AND wp.received_time >= '2026-01-20 23:59:59' 
               ) AS sub_query 
               -- 统一过滤规则：所有类型均只保留最新1条 
            WHERE 
               row_num = 1 
            ORDER BY 
               设备编号, 数据类型, 数值名称, 最后上报时间 DESC;
        """
        
        # 构建查询参数
        like_pattern = f'%{building_name}%'
        cur.execute(sql, (like_pattern, like_pattern, like_pattern, like_pattern, like_pattern))
        
        results = cur.fetchall()
        
        # 转换结果为JSON格式
        rows = []
        for row in results:
            rows.append({
                '设备编号': row[0],
                '点位名称': row[1],
                '设备类别': row[2],
                '数值名称': row[3],
                '数值': row[4],
                '最后上报时间': row[5]
            })
        
        cur.close()
        conn.close()
        
        return jsonify(rows)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)