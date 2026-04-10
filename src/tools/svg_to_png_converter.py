#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVG 转 PNG 转换器
将下载的 SVG 图标转换为 PNG 格式，并生成不同颜色版本
"""

import os
import logging
from PIL import Image
import cairosvg
from io import BytesIO

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SVGtoPNGConverter:
    """SVG 转 PNG 转换器"""
    
    def __init__(self, input_dir='data/icons_comparison', output_dir='data/icons_png'):
        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def convert_svg_to_png(self, svg_path, png_path, size=40, color='#000000'):
        """
        将 SVG 转换为 PNG
        
        Args:
            svg_path: SVG 文件路径
            png_path: PNG 输出路径
            size: 输出尺寸
            color: 图标颜色
        """
        try:
            # 读取 SVG 内容
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # 替换颜色
            # 常见的 SVG 颜色属性
            svg_content = svg_content.replace('stroke="currentColor"', f'stroke="{color}"')
            svg_content = svg_content.replace('fill="currentColor"', f'fill="{color}"')
            svg_content = svg_content.replace('stroke="black"', f'stroke="{color}"')
            svg_content = svg_content.replace('fill="black"', f'fill="{color}"')
            
            # 转换为 PNG
            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                output_width=size,
                output_height=size
            )
            
            # 保存 PNG
            with open(png_path, 'wb') as f:
                f.write(png_data)
            
            logger.info(f"转换成功: {os.path.basename(png_path)}")
            return True
            
        except Exception as e:
            logger.error(f"转换失败 {svg_path}: {e}")
            return False
    
    def convert_all_icons(self):
        """转换所有下载的 SVG 图标"""
        logger.info("=" * 60)
        logger.info("开始转换 SVG 图标为 PNG...")
        logger.info("=" * 60)
        
        # 颜色定义
        colors = {
            'gray': '#7A7E83',    # 未激活
            'green': '#3cc51f'    # 激活
        }
        
        sources = ['feather', 'heroicons']
        icon_names = ['list', 'add', 'chart', 'settings']
        
        results = []
        
        for source in sources:
            source_dir = os.path.join(self.input_dir, source)
            if not os.path.exists(source_dir):
                continue
            
            logger.info(f"\n处理 {source} 图标...")
            
            # 为每个来源创建输出目录
            output_source_dir = os.path.join(self.output_dir, source)
            os.makedirs(output_source_dir, exist_ok=True)
            
            for icon_name in icon_names:
                svg_file = os.path.join(source_dir, f'{icon_name}.svg')
                
                if not os.path.exists(svg_file):
                    continue
                
                logger.info(f"  转换 {icon_name}...")
                
                # 生成灰色版本
                gray_png = os.path.join(output_source_dir, f'{icon_name}.png')
                self.convert_svg_to_png(svg_file, gray_png, size=40, color=colors['gray'])
                
                # 生成绿色版本
                green_png = os.path.join(output_source_dir, f'{icon_name}-active.png')
                self.convert_svg_to_png(svg_file, green_png, size=40, color=colors['green'])
                
                results.append({
                    'source': source,
                    'name': icon_name,
                    'gray': gray_png,
                    'green': green_png
                })
        
        logger.info("\n" + "=" * 60)
        logger.info(f"转换完成！共 {len(results)} 组图标")
        logger.info(f"保存位置: {self.output_dir}")
        logger.info("=" * 60)
        
        return results


def main():
    """主函数"""
    converter = SVGtoPNGConverter()
    results = converter.convert_all_icons()
    
    if results:
        logger.info("\n已转换的图标:")
        for result in results:
            logger.info(f"  {result['source']}/{result['name']}: 灰色 + 绿色版本")
        
        logger.info("\n下一步:")
        logger.info("  查看 data/icons_png/ 目录，选择你喜欢的图标")
        logger.info("  然后复制到小程序的 static/icons/ 目录")
    else:
        logger.warning("没有找到可转换的 SVG 文件")
        logger.info("请先运行: python src/multi_source_icon_crawler.py")


if __name__ == '__main__':
    main()
