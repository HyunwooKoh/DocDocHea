import os
import numpy as np
import sys
import json
from PIL import Image, ImageDraw, ImageFont

font_size = 24
font = ImageFont.truetype('human_taegothic.ttf', font_size)
font2 = ImageFont.truetype('human_taegothic.ttf', 12)

def draw_character(draw, last_x, last_y, text, font_color, font):
    while True:
        f_box = font.getmask(text).getbbox()
        if f_box is None:
            return None, None, None

        ascent, descent = font.getmetrics()
        (width, baseline), (offset_x, offset_y) = font.font.getsize(text)
        x = last_x
        y_top = last_y  # + ((ascent + descent) // 2)

        draw.text((x, y_top), text, fill=font_color, font=font)

        tl_x = x
        tl_y = y_top + offset_y
        br_x = x + f_box[2]
        br_y = y_top + f_box[1] + f_box[3] + offset_y
        break

    return tl_x, tl_y, br_x, br_y


def do_draw_line(draw, last_x, last_y, text, font_color, font, char_space, return_char_box=False):
    regions = []
    max_y = -1
    if return_char_box:
        for idx in range(len(text)):
            ret = draw_character(draw, last_x, last_y, text[idx], font_color, font)
            if ret[0] is None:
                return None, None
            tl_x, tl_y, br_x, br_y = ret
            last_x = int(br_x + ((br_x - tl_x) * char_space))
            regions.append([tl_x, tl_y, br_x, tl_y, br_x, br_y, tl_x, br_y])

            if max_y < 0 or max_y < br_y:
                max_y = br_y
    else:
        ret = draw_character(draw, last_x, last_y, text, font_color, font)
        if ret[0] is None:
            return None, None
        tl_x, tl_y, br_x, br_y = ret
        # TL, TR, BR, BL
        regions.append([tl_x, tl_y, br_x, tl_y, br_x, br_y, tl_x, br_y])

        if max_y < 0 or max_y < br_y:
            max_y = br_y

    if return_char_box:
        return regions, max_y - regions[0][1]
    else:
        return regions, regions[0][5] - regions[0][1]

def draw_result(result, img1, draw_text=True, cls_colors=None, min_cls=0, orientation=0, text_margin=0):
    if orientation == 1:
        img1 = img1.rotate(180, expand=True)
    elif orientation == 2:
        img1 = img1.rotate(90, expand=True)
    elif orientation == 3:
        img1 = img1.rotate(-90, expand=True)

    img1 = img1.convert('RGB')
    draw1 = ImageDraw.ImageDraw(img1)
    img2 = Image.new(size=(img1.width, img1.height), mode='RGB', color=(255, 255, 255))
    draw2 = ImageDraw.ImageDraw(img2)
    if cls_colors is None:
        cls_colors = [(0, 255, 0)]

    def draw_texts(text_results, version='1', f_color=(0, 0, 0), box_color=(255, 0, 0), line_width=1):
        elems = text_results
        for elem_idx, elem in enumerate(elems):
            d = elem
            pt1 = tuple(d['points'][0])
            pt2 = tuple(d['points'][1])

            cls = int(d['detection']['class'])
            if cls < min_cls:
                continue

            if 'FilterName' in d:
                draw2.text((pt1[0] - 10, pt1[1] - 10), d['FilterName'], fill=(0, 0, 255))

            text = d['recognition']['content']
            draw1.rectangle((pt1, pt2), outline=box_color, width=line_width)
            # draw1.rectangle((pt1, pt2), fill=(255, 255, 255), width=3)
            if draw_text and text.strip() != '':
                # Draw text and paste into a detection area
                if 'D' == 'D':
                    if draw_text and text.strip() != '':
                        temp = Image.new(size=(int(img1.width * 2.5), 200), mode='RGB', color=(255, 255, 255))
                        temp_draw = ImageDraw.ImageDraw(temp)
                        rect, h = do_draw_line(temp_draw, 5, 5, text, f_color, font, 0.1)
                        r = rect[0]
                        temp = temp.crop((r[0], r[1], r[4], r[5]))

                        target_w = pt2[0] - pt1[0]
                        target_h = pt2[1] - pt1[1]

                        if target_w - text_margin > 5 and target_h - text_margin > 5:
                            target_w -= text_margin
                            target_h -= text_margin

                        temp = temp.resize((target_w, target_h))
                        mask = np.array(temp).astype(np.uint8)[:, :, 0]
                        mask = mask < 200
                        mask = Image.fromarray(mask)
                        img2.paste(temp, box=(pt1[0], pt1[1], pt1[0] + target_w, pt1[1] + target_h), mask=mask)
                        if '' == 'D':
                            if not 'FilterName' in d:
                                draw2.text((pt1[0], pt1[1] - 10), str(elem_idx), fill=(255, 0, 0), font=font2)

                # Just draw text
                else:
                    draw2.text((pt1[0], pt1[1]), text, fill=(0, 0, 0), font=font2)

                if 'masking' in d:
                    masking_result = d['masking']
                    for mask in masking_result.values():
                        points = mask['points']
                        for pt1, pt2 in points:
                            draw1.rectangle((tuple(pt1), tuple(pt2)), outline=(255, 0, 0), width=2)

    page_elems = result['document']['pages'][0]['elements']
    for elem_idx, page_elem in enumerate(page_elems):
        if page_elem['type'] == 'word':
            pts = page_elem['points']
            # draw1.text((pts[0][0], pts[0][1] - 20), str(elem_idx), fill=(255, 0, 0), font=font2)
            draw_texts([page_elem], version='2', f_color=(0, 0, 0), box_color=(0, 255, 0), line_width=2)
        elif page_elem['type'] == 'textline':
            pts = page_elem['points']
            draw_texts(page_elem['texts'], version='2', f_color=(0, 0, 0), box_color=(0, 150, 255), line_width=1)
            # draw1.text((pts[0][0], pts[0][1] - 20), str(elem_idx), fill=(255, 0, 0), font=font2)
            #draw1.rectangle((tuple(pts[0]), tuple(pts[1])), outline=(0, 255, 0), width=1)
        elif page_elem['type'] == 'table':
            pts = page_elem['points']
            # draw1.text((pts[0][0], pts[0][1] - 20), str(elem_idx), fill=(255, 0, 0), font=font2)
            #draw1.rectangle((tuple(pts[0]), tuple(pts[1])), outline=(0, 0, 255), width=1)
            draw2.rectangle((tuple(pts[0]), tuple(pts[1])), outline=(0, 0, 255), width=1)
            cells = page_elem['cells']
            for cell_idx, cell in enumerate(cells):
                pts = cell['points']
                # draw1.text((pts[0][0], pts[0][1] - 20), '%d-%d' % (elem_idx, cell_idx), fill=(255, 0, 0), font=font2)
                #draw1.rectangle((tuple(pts[0]), tuple(pts[1])), outline=(255, 0, 0), width=1)
                #draw2.rectangle((tuple(pts[0]), tuple(pts[1])), outline=(255, 0, 0), width=1)
                for text_idx, txt_elem in enumerate(cell['texts']):
                    pts = txt_elem['points']
                    if len(cell['texts']) > 1:
                        # draw1.text((pts[0][0], pts[0][1] - 20), '%d-%d-%d' % (elem_idx, cell_idx, text_idx),
                        #            fill=(255, 0, 0), font=font)
                        pass
                    if txt_elem['type'] == 'word':
                        draw_texts([txt_elem], version='2', f_color=(0, 0, 0), box_color=(0, 255, 0), line_width=2)
                    elif txt_elem['type'] == 'textline':
                        draw_texts(txt_elem['texts'], version='2', f_color=(0, 0, 0), box_color=(0, 150, 255), line_width=1)
                        #draw1.rectangle((tuple(pts[0]), tuple(pts[1])), outline=(0, 255, 0), width=1)

    img3 = Image.new(size=(img1.width * 2, img1.height), mode='RGB')
    img3.paste(img1, (0, 0))
    img3.paste(img2, (img1.width, 0))

    return img3


def printUsage():
    print('=============== usage ===============')
    print('draw_image.py  SRC_IMAGE_PATH RESULT_JSON_PATH RESULT_IMAGE_PATH')

if __name__ == "__main__":
    if len(sys.argv) != 4 :
        printUsage()
        exit(0)
    
    image_path = os.path.abspath(sys.argv[1])
    json_path = os.path.abspath(sys.argv[2])
    save_path = os.path.abspath(sys.argv[3])

    if not os.path.exists(image_path) :
        print('Cannot find input image file')
        exit(-100)
    if not os.path.exists(json_path) :
        print('Cannot find result json file')
        exit(-101)
    if os.path.exists(save_path) :
        print('FIle already exist at save path')
        exit (-102)
    
    img = Image.open(open(image_path, 'rb'))
    with open(json_path, 'r', encoding='utf-8') as f:
        jsonData = json.load(f)
    result_img = draw_result(jsonData, img, text_margin=0)
    result_img.save(save_path)