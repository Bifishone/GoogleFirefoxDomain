import time
import random
import os
import sys
import argparse
from colorama import init, Fore, Style
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException
)
from tldextract import extract
from urllib.parse import urlparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr

# 初始化彩色输出
init(autoreset=True)

# 全局配置
MAX_PAGES = 99  # 最大爬取页数
MAX_RETRY = 10  # 域名最大重试次数
SCROLL_PAUSE = 0.3  # 页面滚动等待时间
DEFAULT_PROXY = "127.0.0.1:7890"  # 默认代理地址
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# 全局浏览器实例
driver = None


def print_banner():
    """显示程序横幅"""
    banner = r"""
__________               __  .__                
\______   \ ____   _____/  |_|  |__   ___________
 |     ___// __ \ /    \   __\  |  \_/ __ \_  __ \
 |    |   \  ___/|   |  \  | |   Y  \  ___/|  | \/
 |____|    \___  >___|  /__| |___|  /\___  >__|   
                \/     \/          \/     \/       

    """
    print(Fore.CYAN + banner)
    print(Fore.GREEN + "=" * 60)
    print(Fore.GREEN + "  Google子域名爬取器 - 辉小鱼")
    print(Fore.GREEN + "  功能：默认代理 + 红色子域名 + 批量处理")
    print(Fore.GREEN + "=" * 60)
    print(Style.RESET_ALL)


def check_environment():
    """检查运行环境"""
    print(Fore.YELLOW + "[+] 检查运行环境...")
    # Python版本检查
    if sys.version_info < (3, 7):
        print(Fore.RED + f"[-] 请使用Python 3.7+ (当前: {sys.version.split()[0]})")
        return False
    # 依赖库检查
    required_libs = ['selenium', 'tldextract', 'colorama']
    for lib in required_libs:
        try:
            __import__(lib)
            print(Fore.GREEN + f"[✓] {lib} 已安装")
        except ImportError:
            print(Fore.RED + f"[-] 缺少 {lib}，请运行: pip install {lib}")
            return False
    return True


def find_chromedriver():
    """查找ChromeDriver"""
    print(Fore.YELLOW + "[+] 查找ChromeDriver...")
    from shutil import which
    # 检查系统PATH
    chromedriver = which("chromedriver")
    if chromedriver:
        print(Fore.GREEN + f"[✓] 在PATH中找到: {chromedriver}")
        return chromedriver
    # 检查当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    chromedriver_exe = os.path.join(current_dir, "chromedriver.exe" if os.name == 'nt' else "chromedriver")
    if os.path.exists(chromedriver_exe):
        print(Fore.GREEN + f"[✓] 在当前目录找到: {chromedriver_exe}")
        return chromedriver_exe
    # 未找到提示
    print(Fore.RED + "[-] 未找到ChromeDriver！")
    print(Fore.YELLOW + "[*] 请从 https://chromedriver.chromium.org/ 下载对应版本")
    return None


def setup_driver(proxy=None):
    """初始化浏览器（防指纹 + 默认代理）"""
    global driver
    if driver:
        print(Fore.YELLOW + "[+] 复用浏览器实例")
        return driver

    # 使用默认代理（除非用户指定）
    proxy_to_use = proxy if proxy else DEFAULT_PROXY

    # 查找ChromeDriver
    chromedriver_path = find_chromedriver()
    if not chromedriver_path:
        raise FileNotFoundError("ChromeDriver未找到")

    # 浏览器配置
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")

    # 应用代理
    options.add_argument(f"--proxy-server=http://{proxy_to_use}")
    print(Fore.YELLOW + f"[+] 使用代理: {proxy_to_use}")

    # 启动浏览器
    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(5)  # 缩短页面加载超时时间

        # 隐藏自动化特征
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        })

        print(Fore.GREEN + "[✓] 浏览器启动成功")
        return driver
    except WebDriverException as e:
        print(Fore.RED + f"[-] 浏览器启动失败: {e}")
        raise


def force_scroll(driver):
    """滚动页面加载内容"""
    print(Fore.YELLOW + "[+] 加载页面内容...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(6):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
    print(Fore.YELLOW + "[+] 页面内容加载完成")


def extract_subdomains(driver, query, base_domain):
    """提取子域名（多选择器适配不同页面）"""
    subdomains = set()
    # 多选择器策略，提高兼容性
    selectors = [
        'div.tF2Cxc a[data-ved]',  # 主流结果
        'div.g a[data-ved]',  # 备用结果
        'div.yuRUbf a[href]'  # 移动端结果
    ]
    for selector in selectors:
        try:
            links = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
            )
            for link in links:
                href = link.get_attribute('href')
                if href:
                    parsed = urlparse(href)
                    extracted = extract(parsed.netloc)
                    full_domain = f"{extracted.subdomain}.{extracted.domain}.{extracted.suffix}"
                    if full_domain.endswith(base_domain) and full_domain != base_domain:
                        subdomains.add(full_domain)
            if subdomains:
                break  # 找到结果，停止尝试其他选择器
        except TimeoutException:
            continue
    return subdomains


def crawl_subdomains(driver, query, proxy=None):
    """主爬取逻辑（含空白页面检测）"""
    target_domain = query.split(":")[-1].strip()
    all_subdomains = set()
    current_page = 1
    no_new_results_count = 0  # 连续无新结果计数

    # 修改最大连续无结果页数为99
    MAX_CONSECUTIVE_EMPTY_PAGES = 99

    try:
        while current_page <= MAX_PAGES:
            # 访问页面（首页/下一页）
            if current_page == 1:
                driver.get(f"https://www.google.com/search?q={query}")
            else:
                # 检查“下一页”按钮，无则终止
                try:
                    next_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'a#pnnext'))
                    )
                    next_button.click()
                except TimeoutException:
                    print(Fore.RED + f"[-] 第 {current_page} 页：无下一页按钮，结束爬取")
                    break

            # 验证码检测（快速跳过）
            try:
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.ID, "captcha-form"))
                )
                print(Fore.RED + "[!] 遇到验证码，跳过当前域名")
                break
            except TimeoutException:
                pass

            # 滚动加载
            force_scroll(driver)

            # 提取子域名
            current_subdomains = extract_subdomains(driver, query, target_domain)
            new_subdomains = current_subdomains - all_subdomains

            # 空白页面判定：无新子域名 + 连续25页
            if not new_subdomains:
                no_new_results_count += 1
                print(Fore.YELLOW + f"[-] 第 {current_page} 页：无新子域名（连续 {no_new_results_count} 页）")
                if no_new_results_count >= MAX_CONSECUTIVE_EMPTY_PAGES:
                    print(Fore.RED + f"[-] 连续{MAX_CONSECUTIVE_EMPTY_PAGES}页无结果，判定为空白页面，终止爬取")
                    break
            else:
                all_subdomains.update(new_subdomains)
                print(Fore.GREEN + f"[+] 第 {current_page} 页：新增 {len(new_subdomains)} 个子域名")
                # 红色输出新增子域名
                print(Fore.RED + "    新增子域名：")
                for subdomain in new_subdomains:
                    print(Fore.RED + f"      {subdomain}")
                no_new_results_count = 0  # 重置计数

            current_page += 1
            # 随机延迟（模拟人类行为）
            time.sleep(random.uniform(0.1, 0.5))

    except Exception as e:
        print(Fore.RED + f"[-] 爬取异常: {e}")

    return all_subdomains, current_page - 1


def print_results(subdomains, base_domain):
    """打印结果，子域名使用红色输出"""
    if not subdomains:
        print(Fore.RED + "\n[-] 未找到任何子域名，请检查搜索语法或网络")
        return

    print(Fore.GREEN + f"\n[+] 为 {base_domain} 提取到 {len(subdomains)} 个独特子域名:")
    print(Fore.GREEN + "-" * 60)

    # 只显示前20个子域名，避免刷屏
    if len(subdomains) <= 20:
        max_width = max(len(d) for d in subdomains) if subdomains else 0
        columns = 70 // (max_width + 2)

        for i, subdomain in enumerate(sorted(subdomains), 1):
            print(Fore.RED + f"{subdomain:<{max_width + 2}}", end="" if i % columns != 0 else "\n")

        if len(subdomains) % columns != 0:
            print()
    else:
        print(Fore.CYAN + f"[+] 显示前20个子域名（共 {len(subdomains)} 个）:")
        for i, subdomain in enumerate(sorted(subdomains)[:20], 1):
            print(Fore.RED + f"    {i}. {subdomain}")
        print(Fore.CYAN + f"    ... 等 {len(subdomains) - 20} 个子域名")

    print(Fore.GREEN + "-" * 60)


def save_results(subdomains, filename):
    """保存结果到文件"""
    if not subdomains:
        print(Fore.YELLOW + "[!] 无子域名，不保存文件")
        return
    # 创建results目录
    if not os.path.exists("results"):
        os.makedirs("results")
    # 写入文件
    with open(f"results/{filename}", 'w', encoding='utf-8') as f:
        for sub in sorted(subdomains):
            # 去除开头的.
            if sub.startswith('.'):
                sub = sub[1:]
            f.write(sub + "\n")
    print(Fore.GREEN + f"[+] 结果保存到: results/{filename}")


def process_domain(domain, proxy=None):
    """处理单个域名"""
    global driver

    # 初始化浏览器（如果未初始化）
    if not driver:
        driver = setup_driver(proxy)
        if not driver:
            return set(), 0, False  # 返回空结果、0页、处理失败

    query = f"site:{domain}"
    results_file = f"Google_results_{domain}.txt"

    print(Fore.GREEN + f"\n{'=' * 60}")
    print(Fore.GREEN + f"[+] 处理域名: {domain}")
    print(Fore.GREEN + f"{'=' * 60}")

    print(Fore.YELLOW + f"\n[+] 任务配置:")
    print(Fore.YELLOW + f"  - 搜索关键词: {query}")
    print(Fore.YELLOW + f"  - 最大页数: {MAX_PAGES}")
    print(Fore.YELLOW + f"  - 代理: {proxy if proxy else DEFAULT_PROXY}")
    print(Fore.YELLOW + f"  - 结果文件: results/{results_file}")

    # 开始爬取
    print(Fore.YELLOW + "\n[+] 开始爬取...")
    start_time = time.time()

    subdomains = set()
    retry_count = 0
    pages_crawled = 0

    while retry_count < MAX_RETRY:
        try:
            subdomains, pages_crawled = crawl_subdomains(driver, query, proxy)
            break
        except Exception as e:
            print(Fore.RED + f"[-] 重试 {retry_count + 1}/{MAX_RETRY}: {e}")
            retry_count += 1
            time.sleep(0.3)  # 等待5秒后重试

    end_time = time.time()
    elapsed_time = end_time - start_time

    # 保存结果
    save_results(subdomains, results_file)

    # 输出统计信息
    print(Fore.GREEN + f"[+] 爬取完成 | 耗时: {elapsed_time:.2f}秒 | 页数: {pages_crawled} | 子域名: {len(subdomains)}")

    # 打印结果（红色子域名）
    print_results(subdomains, domain)

    return subdomains, pages_crawled, True  # 返回结果、页数、处理成功


def send_email(sender_email, sender_password, receiver_email, subject, content):
    # 创建邮件对象
    message = MIMEMultipart()

    # 使用 formataddr 函数严格按照 RFC 标准格式化 From 字段
    # 发件人姓名（可自定义）
    sender_name = "Python 邮件发送"
    message['From'] = formataddr((str(Header(sender_name, 'utf-8')), sender_email))

    message['To'] = receiver_email  # 直接使用邮箱地址，QQ邮箱不接受 Header 包装
    message['Subject'] = Header(subject, 'utf-8')

    # 添加邮件正文
    message.attach(MIMEText(content, 'plain', 'utf-8'))

    try:
        # 连接QQ邮箱SMTP服务器（SSL加密）
        smtp_obj = smtplib.SMTP_SSL('smtp.qq.com', 465)
        smtp_obj.login(sender_email, sender_password)

        # 发送邮件
        smtp_obj.sendmail(sender_email, [receiver_email], message.as_string())
        print("邮件发送成功！")

    except smtplib.SMTPException as e:
        print(f"邮件发送失败: {e}")

    finally:
        # 关闭连接
        if 'smtp_obj' in locals():
            smtp_obj.quit()


def main():
    print_banner()
    if not check_environment():
        sys.exit(1)

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Google子域名爬取工具')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--domain', type=str, help='单个目标域名（如：example.com）')
    group.add_argument('-f', '--file', type=str, help='包含多个域名的文件路径')
    parser.add_argument('--proxy', type=str, help='覆盖默认代理（默认: 127.0.0.1:7890）')
    args = parser.parse_args()

    # 初始化全局统计
    total_domains = 0
    total_subdomains = 0
    processed_domains = 0

    try:
        if args.domain:
            # 处理单个域名
            total_domains = 1
            domains = [args.domain]
        else:
            # 从文件读取多个域名
            if not os.path.exists(args.file):
                print(Fore.RED + f"[-] 文件不存在: {args.file}")
                sys.exit(1)

            with open(args.file, 'r', encoding='utf-8') as f:
                domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            total_domains = len(domains)
            print(Fore.YELLOW + f"[+] 从文件加载 {total_domains} 个域名")

        # 处理每个域名
        for i, domain in enumerate(domains, 1):
            print(Fore.YELLOW + f"\n[+] 处理域名 {i}/{total_domains}: {domain}")

            subdomains, pages, success = process_domain(domain, args.proxy)

            if success:
                total_subdomains += len(subdomains)
                processed_domains += 1

            # 域名间等待（避免过快）
            if i < total_domains:
                wait_time = random.uniform(0.2, 0.5)
                print(Fore.YELLOW + f"\n[+] 等待 {wait_time:.2f} 秒后处理下一个域名...")
                time.sleep(wait_time)

    finally:
        # 关闭浏览器
        if driver:
            driver.quit()
            print(Fore.YELLOW + "\n[+] 浏览器已关闭")

        # 输出总体统计
        print(Fore.GREEN + f"\n{'=' * 60}")
        print(Fore.GREEN + "[+] 批量处理完成")
        print(Fore.GREEN + f"[+] 总域名数: {total_domains}")
        print(Fore.GREEN + f"[+] 成功处理: {processed_domains}")
        print(Fore.GREEN + f"[+] 总计子域名: {total_subdomains}")
        print(Fore.GREEN + f"{'=' * 60}")

        # 发送邮件
        sender_email = "1794686508@qq.com"  # 你的QQ邮箱地址
        sender_password = "busnjcluyxtlejgc"  # 你的QQ邮箱SMTP授权码
        receiver_email = "shenghui3301@163.com"  # 收件人邮箱地址
        subject = "📧 Chrome的Domain信息收集工作已完成！"  # 邮件主题
        content = f"""
        您好！尊敬的辉小鱼先生！

        关于Chrome的Domain收集工作已全面完成！
        本次共处理 {total_domains} 个域名，成功处理 {processed_domains} 个，总计提取到 {total_subdomains} 个子域名。
        如果你收到了这封邮件，说明Google-Domain-Search.py脚本已运行完毕！

        祝您挖洞愉快，必出高危哦~~~
        GoogleFirefoxDomain 邮件助手
        """
        send_email(sender_email, sender_password, receiver_email, subject, content)


if __name__ == "__main__":
    main()