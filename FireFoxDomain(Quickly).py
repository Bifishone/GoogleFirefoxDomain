import os
import time
import random
import tldextract
import argparse
from colorama import init, Fore, Style
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException
)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr

# 初始化配置
init(autoreset=True)

# 核心配置
SCROLL_PAUSE = 0.25  # 滚动等待时间
CLICK_RETRY = 1  # 按钮点击重试次数
MAX_EMPTY_ATTEMPTS = 99  # 最大连续空结果轮次
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
RESULTS_FOLDER = "results"  # 结果文件夹名称


def print_banner():
    """显示程序横幅"""
    banner = r"""
                                                                                           ):)
                                                                                         (:::(
                                                                                         ):::::)
   _     ___/\\____________________________/))__ _  (:::::::)
 (::(  \ |         __________                                              |...):::::::)
  \::\  (        (__________,)                                          _|\::)
    \::\   )            __            ____________________|\:::|/
      ¯  /¤¤¤¤¤¤(    (   (::( ¯¯)\:::::::::::::::::::::::::::::::::::::\|¯
         /¤¤¤¤¤¤¤\\    \_.\::\   /:::/¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
        /¤¤¤¤¤¤¤¤\ \______/::'/
       /¤¤¤¤¤¤¤¤¤/\ :::::::::::\:/
      /¤¤¤¤¤¤¤¤¤¤):::)¯¯¯¯¯
     /¤¤¤¤¤¤¤¤¤¤/:::/
 _ /¤¤¤¤¤¤¤¤¤¤/:::/
(  ¯¯¯¯¯¯¯¯¯¯¯\::/     BY : Bifish
  ¯¯¯¯¯¯¯¯¯¯¯¯
    """
    print(Fore.CYAN + banner)
    print(Fore.GREEN + "=" * 60)
    print(Fore.YELLOW + "  基于Firefox的子域深度爬取器(性能优化版) - 辉小鱼")
    print(Fore.RED + "  功能：速度优化，性能拉满~~~")
    print(Fore.GREEN + "=" * 60)
    print(Style.RESET_ALL)


def create_results_folder():
    """创建 results 文件夹（若不存在）"""
    if not os.path.exists(RESULTS_FOLDER):
        os.makedirs(RESULTS_FOLDER)
        print(Fore.GREEN + f"[+] 创建结果文件夹: {RESULTS_FOLDER}")


def setup_driver(proxy=None):
    """初始化浏览器并应用反检测配置"""
    service = Service("geckodriver.exe")  # 替换为你的驱动路径
    options = Options()

    # 反检测配置
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--disable-site-isolation-trials")

    # 浏览器指纹伪装
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    options.set_preference("general.useragent.override", USER_AGENT)
    options.set_preference("browser.cache.disk.enable", False)
    options.set_preference("browser.cache.memory.enable", False)

    # 配置代理
    if proxy:
        proxy_parts = proxy.split(':')
        if len(proxy_parts) == 2:
            host, port = proxy_parts
            options.set_preference("network.proxy.type", 1)
            options.set_preference("network.proxy.http", host)
            options.set_preference("network.proxy.http_port", int(port))
            options.set_preference("network.proxy.ssl", host)
            options.set_preference("network.proxy.ssl_port", int(port))
            print(Fore.GREEN + f"[+] 使用代理: {proxy}")
        else:
            print(Fore.YELLOW + f"[-] 代理格式错误: {proxy} (应为 host:port)")

    try:
        driver = webdriver.Firefox(service=service, options=options)
        print("浏览器启动成功")
        return driver
    except Exception as e:
        print(Fore.RED + f"[-] 浏览器启动失败: {e}")
        return None


def safe_click(driver):
    """安全点击"更多结果"按钮"""
    for attempt in range(CLICK_RETRY):
        try:
            # 使用提供的 ID 定位按钮
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "more-results"))
            )

            # 滚动到按钮位置
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", button)

            # 添加随机延迟，更像人类行为
            time.sleep(random.uniform(0.5, 1))

            # 点击按钮
            button.click()

            # 点击后等待页面加载
            time.sleep(random.uniform(0.2, 1))

            print(Fore.GREEN + f"[+] 成功点击'更多结果'按钮，加载更多内容...")
            return True
        except (TimeoutException, StaleElementReferenceException) as e:
            print(Fore.YELLOW + f"[-] 按钮点击失败（尝试 {attempt + 1}/{CLICK_RETRY}），重试中...")
            time.sleep(0.25)
        except Exception as e:
            print(Fore.RED + f"[-] 点击按钮时发生未知错误: {e}")
            return False

    print(Fore.RED + f"[-] 达到最大重试次数，无法加载更多内容")
    return False


def force_scroll(driver):
    """强制滚动页面以确保所有内容加载"""
    print(Fore.YELLOW + "[+] 强制滚动加载页面内容...")

    last_height = driver.execute_script("return document.body.scrollHeight")

    if last_height == 0:
        print(Fore.YELLOW + "[-] 页面为空，跳过滚动加载")
        return

    while True:
        # 滚动到底部
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # 等待页面加载
        time.sleep(SCROLL_PAUSE)

        # 计算新的页面高度
        new_height = driver.execute_script("return document.body.scrollHeight")

        # 如果页面高度没有变化，说明已经到底部
        if new_height == last_height:
            break

        last_height = new_height

    # 额外的小滚动，确保所有元素都被加载
    for i in range(3):
        driver.execute_script(f"window.scrollBy(0, -{random.randint(100, 300)});")
        time.sleep(0.25)
        driver.execute_script(f"window.scrollBy(0, {random.randint(100, 300)});")
        time.sleep(0.25)

    print(Fore.YELLOW + "[+] 页面内容加载完成")


def extract_subdomains(driver, base_domain):
    """提取页面上的所有子域名"""
    subdomains = set()

    # 使用多种选择器策略，提高提取成功率
    selectors = [
        'a[data-testid="result-title-a"]',  # 主要选择器
        'a.result__url',  # 备用选择器
        'a[data-testid="result-extras-url"]'  # 额外备用选择器
    ]

    for selector in selectors:
        try:
            links = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"使用选择器 '{selector}' 找到 {len(links)} 个链接")

            if not links:
                print(f"选择器 '{selector}' 未找到任何链接")
                continue

            for link in links:
                try:
                    href = link.get_attribute('href')
                    if not href or not href.startswith('http'):
                        continue

                    # 解析域名
                    extracted = tldextract.extract(href)
                    full_domain = f"{extracted.subdomain}.{extracted.domain}.{extracted.suffix}"

                    # 过滤无效域名
                    if not extracted.domain or not extracted.suffix:
                        continue

                    # 只保留与目标域名相关的子域名
                    if base_domain in full_domain and full_domain != base_domain:
                        subdomains.add(full_domain)
                except StaleElementReferenceException:
                    print("元素已过期，跳过")
                    continue

            # 如果使用某个选择器找到了链接，就不再尝试其他选择器
            if links:
                break
        except Exception as e:
            print(f"选择器 '{selector}' 执行出错: {e}")

    print(f"总共提取到 {len(subdomains)} 个子域名")
    return subdomains


def crawl_subdomains(driver, query, proxy=None):
    """主爬取逻辑"""
    # 从查询中提取目标域名
    target_domain = query.split(":")[-1].strip()
    if not target_domain:
        print(Fore.RED + "[-] 无效域名！")
        return set(), 0

    # 构建搜索URL
    search_url = f"https://duckduckgo.com/?q=site:{target_domain}&ia=web"

    try:
        driver.get(search_url)
        print(Fore.GREEN + f"[+] 已打开搜索页: {search_url}")
    except Exception as e:
        print(Fore.RED + f"[-] 打开搜索页失败: {e}")
        return set(), 0

    # 预留时间处理验证码
    print(Fore.YELLOW + "[!] 若出现验证码，请手动完成验证，0.1秒后继续...【因为基本不会出现验证码，后续会优化~~~】")
    time.sleep(0.1)

    all_subdomains = set()
    page_count = 1
    empty_attempts = 0
    start_time = time.time()

    try:
        while empty_attempts < MAX_EMPTY_ATTEMPTS:
            print(Fore.YELLOW + f"\n[+] 第 {page_count} 轮爬取 | 开始加载内容...")

            # 1. 强制滚动加载页面内容
            force_scroll(driver)

            # 2. 提取子域名
            current_subdomains = extract_subdomains(driver, target_domain)
            new_subdomains = current_subdomains - all_subdomains

            # 3. 处理提取结果
            if new_subdomains:
                all_subdomains.update(new_subdomains)
                empty_attempts = 0  # 重置空结果计数器

                print(
                    Fore.GREEN + f"[+] 第 {page_count} 轮 | 新增 {len(new_subdomains)} 个子域名 | 累计 {len(all_subdomains)}")

                # 显示新增子域名
                print(Fore.CYAN + "[+] 新增子域名列表：")
                for idx, subdomain in enumerate(sorted(new_subdomains), 1):
                    print(Fore.CYAN + f"    {idx}. {subdomain}")
            else:
                empty_attempts += 1
                print(
                    Fore.YELLOW + f"[-] 第 {page_count} 轮 | 未发现新子域名 | 空轮次 {empty_attempts}/{MAX_EMPTY_ATTEMPTS}")

            # 4. 移除临时文件保存逻辑

            # 5. 尝试点击"更多结果"按钮
            if not safe_click(driver):
                print(Fore.YELLOW + "[-] 无法加载更多内容，结束爬取")
                break

            page_count += 1
    except Exception as e:
        print(Fore.RED + f"[-] 爬取过程中出现异常: {e}")

    crawl_time = time.time() - start_time
    print(
        Fore.GREEN + f"\n[+] {target_domain} 爬取完成 | 总子域名数量: {len(all_subdomains)} | 耗时: {crawl_time:.2f} 秒")

    return all_subdomains, crawl_time


def save_results(subdomains, filename="results.txt"):
    """保存结果到文件"""
    # 创建results文件夹
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    # 拼接完整路径
    full_path = os.path.join(results_dir, filename)
    try:
        if subdomains:  # 只在有结果时保存文件
            with open(full_path, 'w', encoding='utf-8') as f:
                for domain in subdomains:
                    # 去除开头的.
                    if domain.startswith('.'):
                        domain = domain[1:]
                    f.write(domain + '\n')
            print(Fore.YELLOW + f"[+] 已保存 {len(subdomains)} 个子域名到 {full_path}")
            return True
        else:
            print(Fore.YELLOW + f"[!] 没有找到子域名，不会生成文件")
            return False
    except Exception as e:
        print(Fore.RED + f"[-] 保存文件时出错: {str(e)}")
        return False


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


if __name__ == "__main__":
    # 严格保持原有参数不变
    parser = argparse.ArgumentParser(description='子域深度爬取工具（修复版）')
    parser.add_argument('--command', type=str, help='目标域名（格式：site:example.com）')
    parser.add_argument('-f', type=str, help='包含域名的文件路径')
    parser.add_argument('--proxy', type=str, help='使用代理服务器（格式：host:port）')
    args = parser.parse_args()

    print_banner()
    create_results_folder()

    proxy = args.proxy

    # 初始化浏览器
    driver = setup_driver(proxy)
    if not driver:
        import sys

        sys.exit(1)

    # 用于存储所有爬取结果的字典
    all_results = {}
    total_time = 0

    try:
        if args.f:
            if not os.path.exists(args.f):
                print(Fore.RED + f"[-] 文件 {args.f} 不存在！")
                sys.exit(1)
            with open(args.f, 'r', encoding='utf-8') as f:
                domains = f.read().splitlines()
            for domain in domains:
                command = f"site:{domain}"
                target_domain = domain
                print(Fore.GREEN + f"[+] 开始爬取 {target_domain} 的子域名...")

                subdomains, crawl_time = crawl_subdomains(driver, command, proxy)
                total_time += crawl_time

                # 保存结果
                results_file = f"FireFox_results_{target_domain}.txt"
                save_results(subdomains, results_file)

                # 保存到总结果
                all_results[target_domain] = {
                    'subdomains': subdomains,
                    'count': len(subdomains),
                    'time': crawl_time,
                    'file': results_file
                }

                # 准备下一个域名，不关闭浏览器
                print(Fore.YELLOW + f"\n[+] 准备爬取下一个域名，保持浏览器打开...")

        elif args.command:
            target_domain = args.command.split(":")[-1].strip()
            if not target_domain:
                print(Fore.RED + "[-] 域名不能为空！")
                exit(1)

            print(Fore.GREEN + f"[+] 开始爬取 {target_domain} 的子域名...")

            subdomains, crawl_time = crawl_subdomains(driver, args.command, args.proxy)
            total_time += crawl_time

            # 保存结果
            results_file = f"FireFox_results_{target_domain}.txt"
            save_results(subdomains, results_file)

            # 保存到总结果
            all_results[target_domain] = {
                'subdomains': subdomains,
                'count': len(subdomains),
                'time': crawl_time,
                'file': results_file
            }
        else:
            print(Fore.RED + "[-] 请提供 --command 或 -f 参数！")

        # 生成邮件内容
        if all_results:
            email_subject = "📧 Firefox的Domain信息收集工作已完成！"
            email_content = "您好！尊敬的辉小鱼先生！\n\n"
            email_content += "所有Domain收集工作已全面完成！以下是详细报告：\n\n"

            total_subdomains = 0

            for domain, info in all_results.items():
                email_content += f"🔍 目标域名: {domain}\n"
                email_content += f"   - 子域名数量: {info['count']}\n"
                email_content += f"   - 爬取耗时: {info['time']:.2f} 秒\n"
                email_content += f"   - 结果文件: {info['file']}\n\n"
                total_subdomains += info['count']

            email_content += f"📊 总计爬取域名数: {len(all_results)}\n"
            email_content += f"📊 总子域名数量: {total_subdomains}\n"
            email_content += f"🕒 总耗时: {total_time:.2f} 秒\n\n"

            email_content += "祝您挖洞愉快，必出高危哦~~~\nGoogleFirefoxDomain 邮件助手"

            # 发送邮件通知
            sender_email = "1794686508@qq.com"  # 你的QQ邮箱地址
            sender_password = "busnjcluyxtlejgc"  # 你的QQ邮箱SMTP授权码
            receiver_email = "shenghui3301@163.com"  # 收件人邮箱地址

            send_email(sender_email, sender_password, receiver_email, email_subject, email_content)
        else:
            print(Fore.YELLOW + "[!] 没有爬取任何域名，不会发送邮件")

    finally:
        # 确保最后关闭浏览器
        if driver:
            try:
                driver.quit()
                print(Fore.YELLOW + "[+] 主程序中 Firefox 浏览器已关闭")
            except Exception as e:
                print(Fore.RED + f"[-] 关闭浏览器时出错: {str(e)}")