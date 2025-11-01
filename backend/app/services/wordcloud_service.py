"""
词云生成服务
用于生成学习笔记的词云图
"""

import io
import os
import random
import jieba
import numpy as np
from flask import current_app
from PIL import Image
from wordcloud import WordCloud
from app.models import Stage, LogEntry


def _load_stopwords():
    """从静态文件夹加载所有指定的停用词文件"""
    stopwords = set()
    stopwords_files = [
        'cn_stopwords.txt',
        'baidu_stopwords.txt',
        'hit_stopwords.txt',
        'scu_stopwords.txt',
        'custom_stopwords.txt'
    ]
    
    # 获取backend/static目录
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    static_folder = os.path.join(backend_dir, 'static')
    
    for filename in stopwords_files:
        stopwords_path = os.path.join(static_folder, filename)
        if os.path.exists(stopwords_path):
            try:
                with open(stopwords_path, 'r', encoding='utf-8') as f:
                    stopwords.update([line.strip() for line in f if line.strip()])
            except Exception as e:
                if current_app:
                    current_app.logger.warning(f"Error loading stopwords from {filename}: {e}")
        else:
            if current_app:
                current_app.logger.warning(f"Stopwords file not found: {stopwords_path}")
    
    return stopwords


def _get_mask_image(mask_name='random', width=800, height=800):
    """
    从静态文件夹加载一个指定的或随机的遮罩图片
    强制将图片缩放到指定尺寸,并自动处理透明背景
    """
    try:
        # 获取backend/static目录
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        static_folder = os.path.join(backend_dir, 'static')
        masks_dir = os.path.join(static_folder, 'images', 'masks')
        
        available_masks = [
            'arrow-growth.png', 'bar-chart.png', 'book-open.png', 'brain-profile.png',
            'code-brackets.png', 'dialogue-bubble.png', 'flask-solid.png', 'gear-solid.png',
            'graduation-cap.png', 'key-solid.png', 'laptop-solid.png', 'lightbulb-on.png', 
            'microscope.png', 'puzzle-piece.png', 'tree-of-knowledge.png', 'trophy-solid.png'
        ]

        if not available_masks:
            raise FileNotFoundError("No mask images found in the masks directory.")

        selected_mask_file = mask_name
        if mask_name == 'random' or not mask_name or mask_name not in available_masks:
            selected_mask_file = random.choice(available_masks)

        mask_path = os.path.join(masks_dir, selected_mask_file)

        if not os.path.exists(mask_path):
            if current_app:
                current_app.logger.warning(
                    f"Specified mask '{mask_name}' not found at {mask_path}. "
                    f"Falling back to random."
                )
            selected_mask_file = random.choice(available_masks)
            mask_path = os.path.join(masks_dir, selected_mask_file)

        with Image.open(mask_path) as original_mask_img:
            # 强制将图片缩放到目标尺寸,忽略原始宽高比
            resized_img = original_mask_img.resize((width, height), Image.Resampling.LANCZOS)

            # 处理RGBA透明通道
            if resized_img.mode == 'RGBA':
                background = Image.new("RGB", resized_img.size, (255, 255, 255))
                background.paste(resized_img, (0, 0), resized_img)
                final_mask_img = background
            else:
                final_mask_img = resized_img.convert('RGB')

        return np.array(final_mask_img)

    except Exception as e:
        if current_app:
            current_app.logger.error(f"Error loading and processing mask: {e}", exc_info=True)
        # 返回一个使用正确尺寸的白色背景作为后备
        return np.array(Image.new('RGB', (width, height), (255, 255, 255)))


def get_color_func(palette='default'):
    """
    根据调色板名称返回一个自定义的颜色函数
    """
    palettes = {
        'default': ["#4B0082", "#8A2BE2", "#9932CC", "#BA55D3", "#C71585"],
        'primary_gradient': ["#E0BBE4", "#957DAD", "#D291BC", "#FEC8D8", "#FFDFD3"],
        'inspiration': ["#FFD700", "#FFA500", "#FF8C00", "#FF4500", "#FF6347"],
        'calm': ["#B0E0E6", "#ADD8E6", "#87CEEB", "#87CEFA", "#00BFFF"],
        'forest': ["#90EE90", "#3CB371", "#2E8B57", "#006400", "#556B2F"]
    }
    colors = palettes.get(palette, palettes['default'])

    def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        return random.choice(colors)

    return color_func


def generate_wordcloud_for_user(user_id, stage_id=None, mask_name='random', palette='default'):
    """
    为用户生成一个美化的词云图片
    
    Args:
        user_id: 用户ID
        stage_id: 阶段ID (可选)
        mask_name: 遮罩图片名称
        palette: 调色板名称
        
    Returns:
        BytesIO: 包含PNG图片的缓冲区, 如果失败返回None
    """
    # 查询用户的学习记录
    query = LogEntry.query.join(Stage).filter(Stage.user_id == user_id)
    
    if stage_id and stage_id != 'all':
        query = query.filter(Stage.id == stage_id)

    notes_list = [log.notes for log in query.all() if log.notes and log.notes.strip()]
    
    if not notes_list:
        if current_app:
            current_app.logger.info(f"No notes found for user {user_id}")
        return None

    # 加载停用词
    stopwords = _load_stopwords()
    
    # 合并所有笔记
    full_text = ' '.join(notes_list)
    
    # 使用jieba分词
    word_list = jieba.cut(full_text)

    # 过滤停用词和单字
    filtered_words = [
        word for word in word_list 
        if word not in stopwords and len(word) > 1 and word.strip()
    ]
    
    if not filtered_words:
        if current_app:
            current_app.logger.info(f"No valid words after filtering for user {user_id}")
        return None
        
    segmented_text = ' '.join(filtered_words)

    # 查找字体文件
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    static_folder = os.path.join(backend_dir, 'static')
    font_path = os.path.join(static_folder, 'fonts', 'NotoSansSC-Regular.ttf')
    
    if not os.path.exists(font_path):
        if current_app:
            current_app.logger.error(f"Font file not found: {font_path}")
        return None

    # 定义词云图尺寸
    wc_width, wc_height = 800, 800

    # 获取已缩放的遮罩图片
    mask_image = _get_mask_image(mask_name, width=wc_width, height=wc_height)
    color_function = get_color_func(palette)

    try:
        wordcloud = WordCloud(
            font_path=font_path,
            width=wc_width,
            height=wc_height,
            background_color='rgba(255, 255, 255, 0)',
            mode='RGBA',
            mask=mask_image,
            color_func=color_function,
            prefer_horizontal=0.95,
            collocations=False,
            margin=10,
            max_words=250
        ).generate(segmented_text)

        img_buffer = io.BytesIO()
        wordcloud.to_image().save(img_buffer, format='PNG')
        img_buffer.seek(0)
        return img_buffer

    except Exception as e:
        if current_app:
            current_app.logger.error(f"Failed to generate word cloud: {e}", exc_info=True)
        return None
