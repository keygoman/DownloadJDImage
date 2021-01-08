from lxml import etree
import aiohttp #异步http协议框架
import asyncio #异步框架
import xlrd
import os

sem = asyncio.Semaphore(5) #设置信号量，控制协程数，防止访问过快
header = {'Cookie':'OCSSID=4df0bjva6j7ejussu8al3eqo03','User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36''(KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}

# 获取Excel中商品的skuid
def get_prodcut_skuId():
    product_ids = []
    excel_data = xlrd.open_workbook('./Jd_products.xlsx')
    table = excel_data.sheets()[0]
    nrows = table.nrows
    i = 1
    while i < nrows:
        product_ids.append(int(table.cell_value(i,0)))
        i = i + 1
    return product_ids

# 获取一个skuid的商品全部主图地址
async def get_img_address(skuId):
    img_list = []
    async with sem:
        #asyncio with是异步上下文管理器
        async with aiohttp.ClientSession() as session1:
            async with session1.request('GET',url='https://item.jd.com/'+str(skuId)+'.html',headers = header) as resp:
                html = await resp.read()
                ul= etree.HTML(html).xpath('//*[@id="spec-list"]/ul/li/img')
                for li in ul:
                    temp_address = str(li.get('src')).replace('n5','imgzone',1)
                    # img_address.replace('n5','imgzone',1)
                    img_address = temp_address.replace('s50x64_','',1)
                    img_list.append(img_address)
                if len(img_list) != 0:
                    count = 1
                    for img in img_list:
                        async with session1.get(url='https:'+img,headers=header) as image:
                            imgcontent = await image.read()
                            with open('./'+str(skuId)+'/'+str(count)+'.jpg','wb') as f:
                                f.write(imgcontent)
                        count = count + 1        

# # 下载单张图片方法
# async def download_img(img_list,product_id):
#     count = 1
#     for img_address in img_list:
#         async with sem:
#             async with aiohttp.ClientSession() as session2:
#                 async with session2.request('GET',url=img_address,headers=header) as img_resp:
#                     with open('./'+str(product_id)+'/'+str(count)+'.jpg','wb') as f:
#                         f.write(img_resp.content)
#         count = count + 1

def main():
    product_ids = get_prodcut_skuId()
    if len(product_ids) != 0:
        for id in product_ids:
            try:
                os.mkdir('./'+str(id)+'/')
            except FileExistsError as identifier:
                pass    
    else:
        print('都没东西，你玩你m呢')
    loop = asyncio.get_event_loop()
    tasks = [get_img_address(id) for id in product_ids]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

if __name__ == '__main__':
    main()
