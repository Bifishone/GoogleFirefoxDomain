import colorama
from colorama import Fore, Style

# 初始化 colorama
colorama.init(autoreset=True)

# 定义图案字符串
pattern = r"""
             ¸,a,¸                       ¸a¢$$$*´
                *&a¸                ¸a¢$$$a*
                  &$*a            ¢&$$$$a
                ¢$$$$$        ¢$a*$$$$$a
          ¸,a*$$$$$$¢     ¢$´     *a$$$$a
       a*$$$$$$ƒ*$$$¸a*$         &$$$$$*a
     ¢$$$$$$$¢  ¢$$$$$         ¢$$$$$$$$&a¸
    $$$$$$$$&  &$$a*        ¸a$$$$$$$$$$$$$*a
    $$$$$$$$$    `**´         $$$$$$$$$$$$$$$$$$
     *¸$$$$$$$&               $$$$$$$$$$$$$$$$$$'$
    a*$$$$$$$$$a             &$$$$$$$$$$$$$$$$$$
 a*$$$$$$$$$$$$&            *$$$$$$$$$$$$$$$$$*
 *$$$$$$$$$$$$$$$a,¸          *a$$$$$$$$$$$¢a*
   `*a$$$$$$$$$$$a*´¨               * a$$$$$$$&
        `*·a$$$$$a*                           `*·a$$*&¸
             `*****´                                    `*ªa$a,¸
                                                 ¸a$*`
                                                a$$$a,¸
                                               ¸&$$$$$`*a¸
                                            ¸,a$$$$$$$$$$'$
                           a¢$$&a,¸   ´*a$$$$$$$$$$$$a
                          $$$$$$$$$a¸   *&$$$$$$$$$$$
                           &$$$$ƒ*$$a&,  ¢$$$$$$$$$$*
                             *a$$&  *a$&a*$$$$$$$$$a*
                                *a$$a  `*a$$$$$$$$$a*
                                   *a$$`a·, ¸
      ¸,·a$$$$$$$$$$$a·,¸   `*·a$$$$&*a·,¸
   a$$$$$$$$$$$$$$$$$*a      `*a$$$$$$$*a¸
 *$$$$$$$$$$$$$$$$ƒ*`$$*a       &$$$$$$$$$a¸
  &$$$$$$$$$$$$$$$&   &$$a      *$$$$$$$$$$*a
    *a$$$$$$$$$$$$$$$a   *$$&     a$$$$$$$$$$$&
       *a$$$$$$$$$$$$$$*a  *a$a,¸&$$$$$$$$$$$$a
          *a$$$$$$$$$$$$$$&  `*a$$$$$$$$$$$$$a*
           ¢$$$$$$$$$$$$$$a*     `*·a$$$$$$$a·*´
       ¸,a*$$$$$$$$$$$$¸a*´            `********´
    ´'*·a$$$$$$$$$$¸a·ª´
          `************´                        Bifish™
                           ¸a¢$$$$a¸
                        a*$$$$$$$$*a
                      &$$$$$$$$$$$&
                    ¢$$$$$$$$$$$$$$*a¸
                   a$$$$$$$$$$$$$$$$$`*a¸
                  &$$$$$$$$ƒ*·¸$$$$$$$$$$$a¸
                  $$$$$$$$$¢    &$$$$$$$$$$$&¸
                  $$$$$$$$$&    a$$$$$$$$$$$$$
                  *$$$$$$$$$*a,¸ƒ$$$$$$$$$$$$¢
                     *a$$$$$$$$$$$$$$$$$$$$$a
                        `*a$$$$$$$$$$$$$$$$a*´
                            `* ·a$$$$$$$$$a ·*´
                                  ` **********´
                                  ¸a$*`
                                 a$¢
                               ¸&$&
                            ¸a*$$$$a
             ¸a$*a.,¸,a*$$$$$$$$*a¸
           ·* `*$$$$$$$$$$$$$$$$$*a,¸
                 a$$$$$$$ƒ·¸$$$$$$$$$$* a., ¸
                 ¢$$$$$$$a¸,·$$$$$$$$$$$$$$$* a¸
            ¸,a*$$$$$$$$$$$$$$$$$$$$$$$$$$$$$a
      ¸,.a´$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$a
   a*$$$$$$$$$$$$$$$a*´·¸$$$$$$$$$$$$$$$$$$$
 '&$$$$$$$$$$$$$$$¢´      *$$$$$$$$$$$$$$$$$¢
  $$$$$$$$$$$$$$$$&         *$$$$$$$$$$$$$$$a
   *a$$$$$$$$$$$$$$$*a,¸      &$$$$$$$$$$$$a*
      `*a$$$$$$$$$$$$$¸aª*`·   ¢'$$¸aª**ª·&¸,a$¢*
          `*· a$$$$$$$$&*          ¢a·*´            `*ª´
               `***********´            ·*"
"""

# 定义分隔线
separator = r"""
╔══════════════════════════════════════════════╗
║                                              ║
║  """

separator_end = r"""
║                                              ║
╚══════════════════════════════════════════════╝
"""

# 定义作者信息
signature = r"""
Author: Bifish       Me: https://github.com/Bifish0
                          Shell: GoogleFirefoxDomain
"""

# 定义多种颜色
colors = [
    Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE,
    Fore.MAGENTA, Fore.CYAN, Fore.WHITE,
    Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX,
    Fore.LIGHTYELLOW_EX, Fore.LIGHTBLUE_EX,
    Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX
]

# 按行分割图案并为每行分配不同颜色
lines = pattern.split('\n')
colored_lines = []

for i, line in enumerate(lines):
    # 选择颜色，循环使用颜色列表
    color = colors[i % len(colors)]
    colored_lines.append(color + line + Style.RESET_ALL)

# 为分隔线和作者信息设置颜色
sep_color = Fore.LIGHTBLUE_EX
author_color = Fore.LIGHTMAGENTA_EX
link_color = Fore.LIGHTCYAN_EX
shell_color = Fore.LIGHTGREEN_EX

# 美化作者信息
colored_separator = sep_color + separator + Style.RESET_ALL

# 使用固定宽度格式化确保排版整齐
field_width = 10  # 字段宽度，可根据需要调整
value_width = 30  # 值宽度

# 分别为不同部分设置颜色并格式化
author_line = f"{author_color}Author:{Style.RESET_ALL:<{field_width}}{'Bifish':<{value_width}}"
link_line = f"{link_color}Me:{Style.RESET_ALL:<{field_width}}{'https://github.com/Bifish0':<{value_width}}"
shell_line = f"{shell_color}Shell:{Style.RESET_ALL:<{field_width}}{'GoogleFirefoxDomain':<{value_width}}"

# 添加到分隔线内
colored_signature = [
    f"║  {author_line} ║",
    f"║  {link_line} ║",
    f"║  {shell_line}  ║"
]
colored_signature = '\n'.join(colored_signature)

colored_separator_end = sep_color + separator_end + Style.RESET_ALL

# 输出彩色图案和作者信息
print('\n'.join(colored_lines))
print(colored_separator)
print(colored_signature)
print(colored_separator_end)

# 关闭 colorama
colorama.deinit()