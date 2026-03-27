#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将爬取的 SVG 图标应用到小程序
1. 读取 SVG 文件
2. 转换为 PNG（40x40）
3. 生成灰色和绿色两个版本
4. 复制到小程序目录
"""

import os
import re
import shutil
import logging
from PIL import Image, ImageDraw
from xml.etree import ElementTree as ET

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IconApplier:
    """图标应用器"""
    
    def __init__(self, 
                 source_dir='data/icons_comparison',
                 target_dir='../accounting-miniapp/src/static/icons',
                 size=40):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.size = size
        
        # 颜色定义
        self.colors = {
            'gray': '#7A7E83',    # 未激活
            'green': '#3cc51f'    # 激活
        }
        
        # 确保目标目录存在
        os.makedirs(self.target_dir, exist_ok=True)
    
    def svg_to_png_simple(self, svg_path, png_path, color, size=40):
        """
        简单的 SVG 转 PNG（使用 PIL 绘制基本形状）
        由于 cairosvg 在 Windows 上安装复杂，这里使用简化方案
        """
        try:
            # 读取 SVG 内容
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # 解析 SVG
            root = ET.fromstring(svg_content)
            
            # 创建 PNG 图像
            img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            
            # 转换颜色
            rgb_color = self._hex_to_rgb(color)
            
            # 根据 SVG 内容绘制（简化版）
            # 这里使用启发式方法识别图标类型
            svg_lower = svg_content.lower()
            
            if 'list' in svg_path.lower() or 'menu' in svg_path.lower():
                self._draw_list_icon(draw, size, rgb_color)
            elif 'plus' in svg_path.lower() or 'add' in svg_path.lower():
                self._draw_add_icon(draw, size, rgb_color)
            elif 'chart' in svg_path.lower() or 'bar' in svg_path.lower():
                self._draw_chart_icon(draw, size, rgb_color)
            elif 'cog' in svg_path.lower() or 'settings' in svg_path.lower():
                self._draw_settings_icon(draw, size, rgb_color)
            elif 'home' in svg_path.lower():
                self._draw_home_icon(draw, size, rgb_color)
            elif 'user' in svg_path.lower():
                self._draw_user_icon(draw, size, rgb_color)
            elif 'search' in svg_path.lower():
                self._draw_search_icon(draw, size, rgb_color)
            elif 'heart' in svg_path.lower():
                self._draw_heart_icon(draw, size, rgb_color)
            else:
                # 默认：绘制一个圆形
                center = size // 2
                radius = size // 3
                draw.ellipse(
                    [center - radius, center - radius, center + radius, center + radius],
                    fill=rgb_color
                )
            
            # 保存 PNG
            img.save(png_path, 'PNG')
            logger.info(f"转换成功: {os.path.basename(png_path)}")
            return True
            
        except Exception as e:
            logger.error(f"转换失败 {svg_path}: {e}")
            return False
    
    def _draw_list_icon(self, draw, size, color):
        """绘制列表图标"""
        line_height = 3
        spacing = 6
        start_y = (size - (3 * line_height + 2 * spacing)) // 2
        margin = 8
        
        for i in range(3):
            y = start_y + i * (line_height + spacing)
            draw.rectangle([margin, y, size - margin, y + line_height], fill=color)
    
    def _draw_add_icon(self, draw, size, color):
        """绘制添加图标"""
        thickness = 4
        length = 20
        center = size // 2
        
        # 横线
        draw.rectangle(
            [center - length // 2, center - thickness // 2,
             center + length // 2, center + thickness // 2],
            fill=color
        )
        # 竖线
        draw.rectangle(
            [center - thickness // 2, center - length // 2,
             center + thickness // 2, center + length // 2],
            fill=color
        )
    
    def _draw_chart_icon(self, draw, size, color):
        """绘制图表图标"""
        bar_width = 5
        spacing = 3
        margin = 8
        base_y = size - margin
        heights = [15, 22, 12]
        start_x = margin
        
        for i, height in enumerate(heights):
            x = start_x + i * (bar_width + spacing)
            draw.rectangle([x, base_y - height, x + bar_width, base_y], fill=color)
    
    def _draw_settings_icon(self, draw, size, color):
        """绘制设置图标"""
        center = size // 2
        outer_radius = 14
        inner_radius = 6
        
        # 外圆
        draw.ellipse(
            [center - outer_radius, center - outer_radius,
             center + outer_radius, center + outer_radius],
            fill=color
        )
        # 内圆（白色）
        draw.ellipse(
            [center - inner_radius, center - inner_radius,
             center + inner_radius, center + inner_radius],
            fill=(255, 255, 255, 255)
        )
        
        # 齿轮的齿
        tooth_width = 4
        tooth_length = 4
        
        # 上下左右四个齿
        positions = [
            (center - tooth_width // 2, center - outer_radius - tooth_length,
             center + tooth_width // 2, center - outer_radius),
            (center - tooth_width // 2, center + outer_radius,
             center + tooth_width // 2, center + outer_radius + tooth_length),
            (center - outer_radius - tooth_length, center - tooth_width // 2,
             center - outer_radius, center + tooth_width // 2),
            (center + outer_radius, center - tooth_width // 2,
             center + outer_radius + tooth_length, center + tooth_width // 2)
        ]
        
        for pos in positions:
            draw.rectangle(pos, fill=color)
    
    def _draw_home_icon(self, draw, size, color):
        """绘制首页图标"""
        center = size // 2
        # 绘制房子的三角形屋顶和矩形主体
        # 屋顶
        roof_points = [
            (center, size // 4),
            (size - 8, center),
            (8, center)
        ]
        draw.polygon(roof_points, fill=color)
        
        # 主体
        draw.rectangle([10, center, size - 10, size - 8], fill=color)
        
        # 门（白色）
        door_width = 8
        door_height = 12
        draw.rectangle(
            [center - door_width // 2, size - 8 - door_height,
             center + door_width // 2, size - 8],
            fill=(255, 255, 255, 255)
        )
    
    def _draw_user_icon(self, draw, size, color):
        """绘制用户图标"""
        center = size // 2
        # 头部（圆形）
        head_radius = 6
        draw.ellipse(
            [center - head_radius, 10,
             center + head_radius, 10 + head_radius * 2],
            fill=color
        )
        
        # 身体（半圆/弧形，简化为梯形）
        body_top = 10 + head_radius * 2 + 2
        draw.polygon([
            (center - 10, size - 8),
            (center + 10, size - 8),
            (center + 6, body_top),
            (center - 6, body_top)
        ], fill=color)
    
    def _draw_search_icon(self, draw, size, color):
        """绘制搜索图标"""
        center = size // 2
        # 圆圈
        radius = 10
        thickness = 3
        draw.ellipse(
            [center - radius - 3, center - radius - 3,
             center + radius - 3, center + radius - 3],
            outline=color, width=thickness
        )
        
        # 手柄
        handle_start = center + radius - 3
        handle_end = size - 8
        draw.line(
            [(handle_start, handle_start), (handle_end, handle_end)],
            fill=color, width=thickness
        )
    
    def _draw_heart_icon(self, draw, size, color):
        """绘制心形图标"""
        # 简化的心形（两个圆+三角形）
        center = size // 2
        radius = 8
        
        # 左圆
        draw.ellipse([center - radius - 4, 12, center - 4, 12 + radius * 2], fill=color)
        # 右圆
        draw.ellipse([center + 4, 12, center + radius + 4, 12 + radius * 2], fill=color)
        # 下三角
        draw.polygon([
            (center - radius - 4, 12 + radius),
            (center + radius + 4, 12 + radius),
            (center, size - 8)
        ], fill=color)
    
    def _hex_to_rgb(self, hex_color):
        """将十六进制颜色转换为 RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def process_icons(self, source='feather', icon_names=None):
        """
        处理图标
        
        Args:
            source: 图标来源（feather, heroicons等）
            icon_names: 要处理的图标名称列表，None表示处理所有
        """
        logger.info("=" * 60)
        logger.info(f"开始处理 {source} 图标...")
        logger.info("=" * 60)
        
        source_path = os.path.join(self.source_dir, source)
        
        if not os.path.exists(source_path):
            logger.error(f"来源目录不存在: {source_path}")
            return []
        
        # 获取所有 SVG 文件
        svg_files = [f for f in os.listdir(source_path) if f.endswith('.svg')]
        
        if icon_names:
            # 过滤指定的图标
            svg_files = [f for f in svg_files if f.replace('.svg', '') in icon_names]
        
        if not svg_files:
            logger.warning(f"没有找到 SVG 文件")
            return []
        
        logger.info(f"找到 {len(svg_files)} 个 SVG 文件")
        
        results = []
        
        for svg_file in svg_files:
            icon_name = svg_file.replace('.svg', '')
            svg_path = os.path.join(source_path, svg_file)
            
            logger.info(f"\n处理: {icon_name}")
            
            # 生成灰色版本
            gray_png = os.path.join(self.target_dir, f'{icon_name}.png')
            success_gray = self.svg_to_png_simple(
                svg_path, gray_png, self.colors['gray'], self.size
            )
            
            # 生成绿色版本
            green_png = os.path.join(self.target_dir, f'{icon_name}-active.png')
            success_green = self.svg_to_png_simple(
                svg_path, green_png, self.colors['green'], self.size
            )
            
            if success_gray and success_green:
                results.append({
                    'name': icon_name,
                    'gray': gray_png,
                    'green': green_png
                })
        
        logger.info("\n" + "=" * 60)
        logger.info(f"处理完成！共 {len(results)} 组图标")
        logger.info(f"保存位置: {self.target_dir}")
        logger.info("=" * 60)
        
        return results


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='将爬取的图标应用到小程序')
    parser.add_argument(
        '--source', '-s',
        default='feather',
        choices=['feather', 'heroicons', 'iconmonstr', 'icons8', 'flaticon'],
        help='图标来源（默认: feather）'
    )
    parser.add_argument(
        '--icons', '-i',
        nargs='+',
        help='指定要处理的图标名称（不指定则处理所有）'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("图标应用工具")
    logger.info("=" * 60)
    logger.info(f"来源: {args.source}")
    if args.icons:
        logger.info(f"指定图标: {', '.join(args.icons)}")
    else:
        logger.info("处理所有图标")
    logger.info("=" * 60)
    
    applier = IconApplier()
    results = applier.process_icons(source=args.source, icon_names=args.icons)
    
    if results:
        logger.info("\n已生成的图标:")
        for result in results:
            logger.info(f"  {result['name']}: 灰色 + 绿色版本")
        
        logger.info("\n下一步:")
        logger.info("  1. 重新编译小程序: cd ../accounting-miniapp && npm run dev:mp-weixin")
        logger.info("  2. 在微信开发者工具中重新导入项目")
        logger.info("  3. 查看新的图标效果！")
    else:
        logger.warning("没有成功处理任何图标")


if __name__ == '__main__':
    main()
