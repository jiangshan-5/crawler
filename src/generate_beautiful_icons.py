#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成漂亮的图标 - 使用 PIL 绘制简单但美观的图标
"""

from PIL import Image, ImageDraw, ImageFont
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IconGenerator:
    """图标生成器"""
    
    def __init__(self, size=40, output_dir='../accounting-miniapp/src/static/icons'):
        self.size = size
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_list_icon(self, color, filename):
        """创建列表图标 - 三条横线"""
        img = Image.new('RGBA', (self.size, self.size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # 转换颜色
        rgb_color = self._hex_to_rgb(color)
        
        # 绘制三条横线
        line_height = 3
        spacing = 6
        start_y = (self.size - (3 * line_height + 2 * spacing)) // 2
        margin = 8
        
        for i in range(3):
            y = start_y + i * (line_height + spacing)
            draw.rectangle(
                [margin, y, self.size - margin, y + line_height],
                fill=rgb_color
            )
        
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath, 'PNG')
        logger.info(f"✓ 创建成功: {filename}")
        return filepath
    
    def create_add_icon(self, color, filename):
        """创建添加图标 - 加号"""
        img = Image.new('RGBA', (self.size, self.size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        rgb_color = self._hex_to_rgb(color)
        
        # 绘制加号
        thickness = 4
        length = 20
        center = self.size // 2
        
        # 横线
        draw.rectangle(
            [center - length // 2, center - thickness // 2,
             center + length // 2, center + thickness // 2],
            fill=rgb_color
        )
        
        # 竖线
        draw.rectangle(
            [center - thickness // 2, center - length // 2,
             center + thickness // 2, center + length // 2],
            fill=rgb_color
        )
        
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath, 'PNG')
        logger.info(f"✓ 创建成功: {filename}")
        return filepath
    
    def create_chart_icon(self, color, filename):
        """创建图表图标 - 柱状图"""
        img = Image.new('RGBA', (self.size, self.size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        rgb_color = self._hex_to_rgb(color)
        
        # 绘制三个柱子
        bar_width = 5
        spacing = 3
        margin = 8
        base_y = self.size - margin
        
        heights = [15, 22, 12]  # 三个柱子的高度
        start_x = margin
        
        for i, height in enumerate(heights):
            x = start_x + i * (bar_width + spacing)
            draw.rectangle(
                [x, base_y - height, x + bar_width, base_y],
                fill=rgb_color
            )
        
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath, 'PNG')
        logger.info(f"✓ 创建成功: {filename}")
        return filepath
    
    def create_settings_icon(self, color, filename):
        """创建设置图标 - 齿轮"""
        img = Image.new('RGBA', (self.size, self.size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        rgb_color = self._hex_to_rgb(color)
        
        center = self.size // 2
        outer_radius = 14
        inner_radius = 6
        
        # 绘制外圆
        draw.ellipse(
            [center - outer_radius, center - outer_radius,
             center + outer_radius, center + outer_radius],
            fill=rgb_color
        )
        
        # 绘制内圆（白色）
        draw.ellipse(
            [center - inner_radius, center - inner_radius,
             center + inner_radius, center + inner_radius],
            fill=(255, 255, 255, 255)
        )
        
        # 绘制齿轮的齿（简化版 - 四个矩形）
        tooth_width = 4
        tooth_length = 4
        
        # 上
        draw.rectangle(
            [center - tooth_width // 2, center - outer_radius - tooth_length,
             center + tooth_width // 2, center - outer_radius],
            fill=rgb_color
        )
        
        # 下
        draw.rectangle(
            [center - tooth_width // 2, center + outer_radius,
             center + tooth_width // 2, center + outer_radius + tooth_length],
            fill=rgb_color
        )
        
        # 左
        draw.rectangle(
            [center - outer_radius - tooth_length, center - tooth_width // 2,
             center - outer_radius, center + tooth_width // 2],
            fill=rgb_color
        )
        
        # 右
        draw.rectangle(
            [center + outer_radius, center - tooth_width // 2,
             center + outer_radius + tooth_length, center + tooth_width // 2],
            fill=rgb_color
        )
        
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath, 'PNG')
        logger.info(f"✓ 创建成功: {filename}")
        return filepath
    
    def _hex_to_rgb(self, hex_color):
        """将十六进制颜色转换为 RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def generate_all_icons(self):
        """生成所有图标"""
        logger.info("=" * 60)
        logger.info("开始生成图标...")
        logger.info("=" * 60)
        
        # 颜色定义
        gray_color = '7A7E83'    # 未激活状态
        green_color = '3cc51f'   # 激活状态
        
        icons = [
            ('list', self.create_list_icon),
            ('add', self.create_add_icon),
            ('chart', self.create_chart_icon),
            ('settings', self.create_settings_icon)
        ]
        
        results = []
        
        for name, create_func in icons:
            logger.info(f"\n生成 {name} 图标...")
            
            # 灰色版本
            gray_file = f'{name}.png'
            create_func(gray_color, gray_file)
            
            # 绿色版本
            green_file = f'{name}-active.png'
            create_func(green_color, green_file)
            
            results.append({
                'name': name,
                'normal': gray_file,
                'active': green_file
            })
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✓ 所有图标生成完成！共 {len(results) * 2} 个文件")
        logger.info(f"✓ 保存位置: {self.output_dir}")
        logger.info("=" * 60)
        
        return results


def main():
    """主函数"""
    generator = IconGenerator(size=40)
    results = generator.generate_all_icons()
    
    logger.info("\n生成的图标:")
    for result in results:
        logger.info(f"  • {result['name']}: {result['normal']}, {result['active']}")
    
    logger.info("\n下一步:")
    logger.info("  1. 重新编译小程序: cd ../accounting-miniapp && npm run dev:mp-weixin")
    logger.info("  2. 在微信开发者工具中重新导入项目")
    logger.info("  3. 查看漂亮的新图标！")


if __name__ == '__main__':
    main()
