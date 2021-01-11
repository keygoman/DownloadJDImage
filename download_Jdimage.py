from lxml import etree #用来解析HTML
import aiohttp #异步http框架
import asyncio #异步框架
import xlrd #读取Excel
import os

sem = asyncio.Semaphore(5) #设置信号量，控制协程数，防止访问过快
header = {'Cookie':'OCSSID=4df0bjva6j7ejussu8al3eqo03','User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36''(KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}

# 获取Excel中商品的skuid
def get_prodcut_skuId():
    product_ids = []
    excel_data = xlrd.open_workbook('./Jd_products.xlsx')
    table = excel_data.sheets()[0]
    nrows = table.nrows #获取有效行数
    i = 1 #i取1即从第二行开始读取，第一行是标题
    while i < nrows:
        product_ids.append(int(table.cell_value(i,0)))
        i = i + 1
    return product_ids

'''
    这个难点就是大图是动态加载的，所以（自认为）很难追踪到图片地址
    因此我是通过找到那个商品的小图（50*50像素），通过修改url获得大图
    将小图（50*50）地址提取出来后，将图片url的‘n5’替换为‘imgzone’，将‘s50x64_’去掉
    就能获得对应商品的800*800像素（最大）的大图地址
'''
# 获取一个skuid的商品全部主图
async def get_image(skuId):
    img_list = []
    # asyncio with是异步上下文管理器,防止协程超过信号量
    async with sem:
        # aiohttp提供ClientSession方法相当于建立session
        async with aiohttp.ClientSession() as session:
            # 异步的request方法
            async with session.request('GET',url='https://item.jd.com/'+str(skuId)+'.html',headers = header) as resp:
                html = await resp.read() #read()直接获取bytes
                # 用xpath筛选出想要的HTML内容，是一个ul，li里面有img标签，标签的src属性是图片地址
                ul= etree.HTML(html).xpath('//*[@id="spec-list"]/ul/li/img')
                # 修改小图的url，得到大图的真实url
                for li in ul:
                    temp_address = str(li.get('src')).replace('n5','imgzone',1)
                    # img_address.replace('n5','imgzone',1)
                    img_address = temp_address.replace('s50x64_','',1)
                    img_list.append(img_address)
                if len(img_list) != 0:
                    count = 1 #用来给下载的图片命名
                    for img in img_list:
                        # 这次直接用get方法算了
                        async with session.get(url='https:'+img,headers=header) as image:
                            imgcontent = await image.read()
                            # with open用完就不用close()方法了,wb是二进制打开只用于写入
                            with open('./'+str(skuId)+'/'+str(count)+'.jpg','wb') as f:
                                f.write(imgcontent)
                        count = count + 1

def main():
    product_ids = get_prodcut_skuId()
    if len(product_ids) != 0:
        # 如果表格获取的内容不为空，则根据这些skuId新建文件夹
        for id in product_ids:
            try:
                os.mkdir('./'+str(id)+'/')
            except FileExistsError as identifier:
                pass    
    else:
        print('表格为空')
    # 新建循环事件，然后添加任务和协程
    loop = asyncio.get_event_loop()
    tasks = [get_image(id) for id in product_ids]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

if __name__ == '__main__':
    main()
