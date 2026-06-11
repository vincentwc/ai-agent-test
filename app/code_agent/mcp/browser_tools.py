"""
Selenium 百度搜索示例
用于演示如何使用 Selenium WebDriver 自动化操作百度搜索
"""
import time

from mcp.server.fastmcp import FastMCP
# Selenium WebDriver 主模块，用于控制浏览器
from selenium import webdriver
# Chrome 浏览器服务类，用于管理 chromedriver 进程
from selenium.webdriver.chrome.service import Service
# 定位符枚举，指定如何查找页面元素（ID、XPath、CSS 等）
from selenium.webdriver.common.by import By
# 显式等待类，等待元素满足条件
from selenium.webdriver.support.wait import WebDriverWait
# 预期条件集合，判断元素状态（元素存在、可点击、可见等）
from selenium.webdriver.support import expected_conditions as EC
# 自动下载匹配 Chrome 版本的 chromedriver
from webdriver_manager.chrome import ChromeDriverManager


# ========== 函数定义 ==========

mcp = FastMCP()

@mcp.tool(description="search query word in Baidu")
def search_in_baidu(query: str):
    """
    在百度搜索指定关键词

    Args:
        query: 要搜索的关键词字符串
    Returns:
        页面内容文本，搜索失败返回 None
    """

    # ========== 配置浏览器选项 ==========

    # 创建 Chrome 选项对象
    options = webdriver.ChromeOptions()

    # 容器/CI 环境必备：禁用沙箱模式（容器内无权限）
    options.add_argument("--no-sandbox")

    # 容器环境优化：禁用 /dev/shm 共享内存（避免内存不足崩溃）
    options.add_argument("--disable-dev-shm-usage")

    # 调试模式：注释掉 headless 可以看到浏览器窗口
    # 正式环境可启用：options.add_argument("--headless=new")
    # options.add_argument("--headless=new")

    # 禁用 GPU 硬件加速（容器/CI 环境无 GPU）
    options.add_argument("--disable-gpu")

    # 禁用软件光栅化（配合 --disable-gpu，减少资源占用）
    options.add_argument("--disable-software-rasterizer")

    # 禁用浏览器扩展程序（减少干扰和资源占用）
    options.add_argument("--disable-extensions")

    # 禁用后台网络请求（减少不必要的网络流量）
    options.add_argument("--disable-background-networking")

    # 禁用默认应用（Chrome 默认启动的应用如登录、欢迎页等）
    options.add_argument("--disable-default-apps")

    # 禁用浏览器同步功能（书签、历史、密码等同步服务）
    options.add_argument("--disable-sync")

    # 禁用翻译提示栏（减少页面元素干扰）
    options.add_argument("--disable-translate")

    # 只记录指标，不上报（减少网络请求）
    options.add_argument("--metrics-recording-only")

    # 静音所有音频（避免自动化过程中播放声音）
    options.add_argument("--mute-audio")

    # 跳过首次运行向导（首次启动时的设置向导）
    options.add_argument("--no-first-run")

    # 禁用 Google 安全浏览自动更新（减少启动时的网络检查）
    options.add_argument("--safebrowsing-disable-auto-update")

    # 关键：禁用自动化控制特征，防止网站检测到 Selenium
    # Blink 引擎的 AutomationControlled 功能会被禁用
    options.add_argument("--disable-blink-features=AutomationControlled")

    # 禁用信息栏（如"Chrome 正在受到自动测试软件控制"的提示）
    options.add_argument("--disable-infobars")

    # 忽略证书错误（访问 HTTPS 时不验证证书）
    options.add_argument("--ignore-certificate-errors")

    # ========== 初始化浏览器驱动 ==========

    # 使用 ChromeDriverManager 自动下载匹配当前 Chrome 版本的 chromedriver
    # 首次运行会从缓存目录缓存，无需重复下载
    service = Service(ChromeDriverManager().install())

    # 创建 Chrome 浏览器实例，传入 service（chromedriver 进程）和 options（配置）
    driver = webdriver.Chrome(service=service, options=options)

    # ========== 防检测：注入 JS 脚本 ==========

    # 通过 CDP (Chrome DevTools Protocol) 在每个新文档加载前执行脚本
    # 将 navigator.webdriver 属性设为 undefined，欺骗网站检测
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
    })

    # ========== 设置显式等待 ==========

    # 创建 WebDriverWait 对象，等待超时时间为 5 秒
    # 每隔 0.5 秒检查一次元素是否满足条件
    wait = WebDriverWait(driver, 5)

    try:
        # ========== 打开百度首页 ==========

        # 导航到百度首页
        driver.get("https://www.baidu.com")

        # ========== 输入搜索关键词 ==========

        # 等待页面中 ID 为 "chat-textarea" 的输入框出现
        # presence_of_element_located: 元素存在于 DOM 中即可（可能不可见）
        text_box = wait.until(
            EC.presence_of_element_located((By.ID, "chat-textarea"))
        )

        # 向输入框发送搜索关键词（模拟键盘输入）
        text_box.send_keys(query)

        # ========== 点击搜索按钮 ==========

        # 等待 ID 为 "chat-submit-button" 的按钮可点击
        # element_to_be_clickable: 元素存在且可见、启用状态
        submit_button = wait.until(
            EC.element_to_be_clickable((By.ID, "chat-submit-button"))
        )

        # 首次点击（Selenium 点击）
        submit_button.click()

        # ========== 等待搜索结果加载 ==========

        # 等待页面标题包含搜索关键词的前 10 个字符（确认搜索完成）
        WebDriverWait(driver, 5).until(
            EC.title_contains(query[:10])
        )

        # ========== 获取并打印页面内容 ==========

        # 翻页优化
        page_text_list = []
        for i in range(3):
            if i > 0:
                # 点击下一页按钮
                results = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".page-inner_2jZi2>a"))
                )
                results[i].click()

            # # 等待 <body> 元素出现在 DOM 中
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # 滚动优化
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)

                # 检查是否加载完成
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # 查找 body 元素
            page_content = driver.find_element(By.TAG_NAME, "body")
            page_text = page_content.text
            page_text_list.append(f'第{i+1}页：\n{page_text}\n --- \n')

        driver.quit()

        # 返回 body 的文本内容（搜索结果）
        # print(page_content.get_attribute("innerHTML"))
        return '\n'.join(page_text_list)

    # ========== 异常处理 ==========

    except Exception as e:
        # 打印异常信息（定位、超时等错误）
        return None



# ========== 程序入口 ==========

if __name__ == '__main__':
    mcp.run(transport="stdio")
    # 当直接运行此文件时执行，作为测试入口
    # 调用搜索函数，搜索"北京的天气"
    # res = search_in_baidu("北京的天气")
    # print(res)