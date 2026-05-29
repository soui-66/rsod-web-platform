\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{xdulabreport}
              [2020/02/02 v2.0 Standard LaTeX Template for xdu lab report]


%%%% 加载文档类和宏包
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{ctexart}}
\ProcessOptions\relax
\LoadClass[a4paper,12pt]{ctexart}
\RequirePackage{ifxetex}
\RequireXeTeX
\ifxetex\else
\ClassError{xdumcmthesis}{You must use the `xelatex' driver\MessageBreak Please choose `xelatex'}{%
	Just choose `xelatex', no `pdflatex' or `latex' and so on.}
\fi
% 页面布局
\RequirePackage{geometry}
% 数学宏包
\RequirePackage{amsmath}
\RequirePackage{amsfonts}
\RequirePackage{amssymb}
\RequirePackage{bm}
\RequirePackage{titletoc}
% 设置颜色
\RequirePackage{xcolor}
% 插入图片
\RequirePackage{graphicx}
% 表格
\RequirePackage{array}
%% 长表格
\RequirePackage{longtable}
%% booktabs 提供了\toprule 等命令.
\RequirePackage{booktabs}
%% multirow 支持在表格中跨行
\RequirePackage{multirow}
%% 调整间隔, 让表格更好看些
\RequirePackage{bigstrut}
%% 在跨行表格中输入定界符
\RequirePackage{bigdelim}
% 保护脆落命令
\RequirePackage{cprotect}
% 设置代码环境
\RequirePackage{listings}
%\RequirePackage{minted}
% 首行缩进
\RequirePackage{indentfirst}
% 设置浮动体的标题
\RequirePackage{caption}
% 定制列表环境
\RequirePackage{enumerate}
\RequirePackage[shortlabels]{enumitem}
% 下划线
\RequirePackage{ulem}
% 尺寸计算
\RequirePackage{calc}
% 目录文字重叠
\RequirePackage{tocloft}
\renewcommand\cftsecnumwidth{3em}
% 去除超链接框
\RequirePackage[colorlinks=true,linkcolor=black]{hyperref}
%\hypersetup{hidelinks}
% logo
\RequirePackage{hologo}
% 制作心得表格使用到的两个包
\RequirePackage{multirow,makecell}
%%%% 预设
\definecolor{dkgreen}{rgb}{0,0.6,0}
\definecolor{gray}{rgb}{0.5,0.5,0.5}
\definecolor{mauve}{rgb}{0.58,0,0.82}

\lstset{
	frame=tb,
	aboveskip=3mm,
	belowskip=3mm,
	showstringspaces=false,
	columns=flexible,
	framerule=1pt,
	rulecolor=\color{gray!35},
	backgroundcolor=\color{gray!5},
	basicstyle={\small\ttfamily},
	numbers=none,
	numberstyle=\tiny\color{gray},
	keywordstyle=\color{blue},
	commentstyle=\color{dkgreen},
	stringstyle=\color{mauve},
	breaklines=true,
	breakatwhitespace=true,
	tabsize=3,
}


% 目录、章节标题格式设置
\ctexset {
	contentsname = {\centerline{目\quad 录}},
	section = {
%		 name = {实训：},
		 number = \chinese{section}, 
		 format = \centering\heiti\zihao{-2},
	 },
 	subsection = {
 		format = \heiti\zihao{-3},
 	},
 	subsubsection = {
 		format = \heiti\zihao{-4},	
 	},
}
% 设置图片、表格、公式
\numberwithin{figure}{section}
\numberwithin{table}{section}
\numberwithin{equation}{section}
%\setCJKmainfont{宋体}
% 设置目录深度
\setcounter{tocdepth}{2}
% 页面布局
\geometry{top=25mm,bottom=25mm,left=25mm,right=25mm}
% 每行缩进两个汉字
%\setlength\parindent{2em}
% 设置字体
\setmainfont{Times New Roman}
\setmonofont{Courier New}
\setsansfont{Arial}





%%%% 封面
%实验课程
\newcommand*\@xdulab@Course{}
%学院名称
\newcommand*\@xdulab@AcademyName{}
%专业
\newcommand*\@xdulab@Profession{}
%姓名
\newcommand*\@xdulab@Name{}
%学号
\newcommand*\@xdulab@Number{}
%任课教师
\newcommand*\@xdulab@Teacher{}
%实验地点
\newcommand*\@xdulab@Place{}
%实验成绩
\newcommand*\@xdulab@Grade{}
%日期
\newcommand*\@xdulab@Fisrtdate{1}
\newcommand*\@xdulab@Lastdate{2}
%









% 浮动环境设置
% 默认情况下, \LaTeX{} 要求每页的文字至少占据 20%,否则该页就只单独放置一个浮动环境,
% 而这通常不是我们想要的, 我们将这个要求降低到 5%.
 \renewcommand*{\textfraction}{0.05}
% 有时如果多个浮动环境连续放在一起, \LaTeX{}
% 会将它们分在几个不同页，即使它们可在同一页放
% 得下. 我们可以通过修改 |\topfraction| 和 |\bottomfraction| 分别设置顶端和底端的浮
% 动环境的最大比例.
 \renewcommand*{\topfraction}{0.9}
 \renewcommand*{\bottomfraction}{0.8}
% 有时\LaTeX{}会把一个浮动环境单独放在一页,
% 我们要求这个环境至少要占据 85% 才能单独放在一页.
% 注意:  |\floatpagefraction| 的数值必须小于 |\topfraction|.
 \renewcommand*{\floatpagefraction}{0.85}
% 关于图片 graphicx
 % 如果图片没有指定后缀, 依次按下列顺序搜索
\DeclareGraphicsExtensions{.png,.jpg,.pdf,.eps}
 % 设置图表搜索路径, 可以给图表文件夹取如下名字
\graphicspath{{figures/}{figure/}{pictures/}%
  {picture/}{pic/}{pics/}{image/}{images/}}
% 图表标题
\DeclareCaptionFont{song}{\songti}
\DeclareCaptionFont{minusfour}{\zihao{-4}}
\captionsetup[figure]{%
	format=hang,   % 标题从第二行开始都有缩进, 应该和 justification=raggedright 的效果一样.
	labelsep=quad, % 分隔符是一个空格
	font={song,minusfour,bf}, % 图的字体, 宋体小四
	position=bottom % position=bottom, 不代表标题放在下面, 标题仍放在你放\caption的位置.
}
\captionsetup[table]{%
	format=hang,   % 标题从第二行开始都有缩进, 应该和 justification=raggedright 的效果一样.
	labelsep=quad, % 分隔符是一个空格
	font={song,minusfour,bf}, % 表的字体, 宋体小四
	position=top % position=bottom, 不代表标题放在下面, 标题仍放在你放\caption的位置.
}
% 列表环境设置
\setlist{%
	topsep=0.3em, % 列表顶端的垂直空白
	partopsep=0pt, % 列表环境前面紧接着一个空白行时其顶端的额外垂直空白
	itemsep=0ex plus 0.1ex, % 列表项之间的额外垂直空白
	parsep=0pt, % 列表项内的段落之间的垂直空白
	leftmargin=1.5em, % 环境的左边界和列表之间的水平距离
	rightmargin=0em, % 环境的右边界和列表之间的水平距离
	labelsep=0.5em, % 包含标签的盒子与列表项的第一行文本之间的间隔
	labelwidth=2em % 包含标签的盒子的正常宽度；若实际宽度更宽，则使用实际宽度。
}

\lstnewenvironment{tcode}
  {
    \lstset{basicstyle = \small\ttfamily,
        language=TeX,
        tabsize = 4,
        frame = single,
        escapechar = `,
        breaklines = true,
        breakatwhitespace = true,
        frameround = tttt,
    }
  }
  {}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Document Markup

% 生成封面, 使用\maketitle
\renewcommand{\maketitle}{\par
	\begingroup
      \newpage
      \global\@topnum\z@   % Prevents figures from going at top of page.
      \@maketitle
    \endgroup
  \global\let\thanks\relax
  \global\let\maketitle\relax
  \global\let\@maketitle\relax
  \global\let\@thanks\@empty
  \global\let\@author\@empty
  \global\let\@date\@empty
%  \global\let\@title\@empty
%  \global\let\title\relax
  \global\let\author\relax
  \global\let\date\relax
  \global\let\and\relax
  \newpage
}
\def\@maketitle{%
  \newpage
 \vskip2ex
  \thispagestyle{empty}
  \begin{center}
      \includegraphics[scale=.9]{logo.pdf} \\
  \end{center}
  \vskip1.5cm
  \begin{center}
      \makebox[109mm][s]{\heiti\zihao{-0}\bf 项目实训总结报告}
  \end{center}
\vskip 3cm
\begin{center}
%    \makebox[20mm][s]{\heiti\zihao{-3} 实训课程}\quad\underline{\makebox[120mm][c]{\heiti\zihao{3} \@xdulab@Course}}\\
%    \vskip1cm
    \makebox[20mm][s]{\heiti\zihao{-3} 实训名称: }\quad\underline{\makebox[120mm][c]{\heiti \zihao{3} \@xdulab@AcademyName}}\\
    \vskip1cm
    \makebox[20mm][s]{\heiti\zihao{-3} 学院名称: }\quad\underline{\makebox[120mm][c]{\heiti\zihao{3}  \@xdulab@Place}}\\
    \vskip1cm
    \makebox[20mm][s]{\heiti\zihao{-3} 专业名称: }\quad\underline{\makebox[120mm][c]{\heiti\zihao{3}  \@xdulab@Profession}}\\
    \vskip1cm
    \makebox[20mm][s]{\heiti\zihao{-3} 学生姓名: }\quad\underline{\makebox[120mm][c]{\heiti\zihao{3} \@xdulab@Name}}\\
    \vskip1cm
    \makebox[20mm][s]{\heiti\zihao{-3} 学生学号: }\quad\underline{\makebox[120mm][c]{\heiti\zihao{3} \@xdulab@Number}}\\
    \vskip1cm
    \makebox[20mm][s]{\heiti\zihao{-3} 指导教师: }\quad\underline{\makebox[120mm][c]{\heiti\zihao{3} \@xdulab@Teacher}}\\
%    \vskip1cm
%    \makebox[20mm][s]{\heiti\zihao{-3} 实验地点}\quad\underline{\makebox[120mm][c]{\heiti\zihao{3} \@xdulab@Place}}
%    \vskip1cm
%    \makebox[20mm][s]{\heiti\zihao{-3} 实训成绩}\quad\underline{\makebox[120mm][c]{\heiti\zihao{3} \@xdulab@Grade}}\\
\end{center}
\vskip1.85cm

\vfill \begin{center}
{\songti\zihao{3}\@xdulab@Fisrtdate---\@xdulab@Lastdate }
\end{center}
\newpage
\tableofcontents
\pagestyle{empty}
\newpage
\pagestyle{plain}
\setcounter{page}{1}
}

\RequirePackage{fancyhdr}
\RequirePackage{fontawesome}
\RequirePackage{xhfill}

\fancyhf{} % 清空默认设置




\fancyhead[R]{\leftmark} % 页眉右边显示章节名称
\renewcommand{\headrulewidth}{0.4pt} % 设置页眉下面的线宽
\fancypagestyle{plain}{\renewcommand{\headrulewidth}{0pt}\fancyhf{}\renewcommand{\headrule}{}}

% 定义页脚
\fancyfoot[c]{第~\color{black}{\thepage}~页 } % 页脚中间显示页码

% 应用fancy样式
\pagestyle{fancy}

% 定义plain样式，用于章节的首页
\fancypagestyle{plain}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \fancyfoot[C]{\thepage}
}



\providecommand{\experience}[1]{
\newpage
\pagestyle{empty}
\renewcommand{\arraystretch}{2}
\begin{table}
	\centering
	\begin{tabular}{|p{0.06\linewidth}<\centering|p{0.9\linewidth}|}
		\hline
		\multirowcell{1}{\textbf{学生}\\\textbf{实验}\\\textbf{心得}}&
		\begin{minipage}[l][12cm][c]{\linewidth}
			\begin{minipage}[l][10cm][c]{\linewidth}\zihao{-4}
				#1
			\end{minipage}
			
			\makebox[\linewidth][r]{\textbf{学生(签名)：}\hspace{2cm}}
			\vskip 0.2cm
			\makebox[\linewidth][r]{\textbf{\today}\hspace{1cm}}
		\end{minipage}
		\\ \hline
		\multirowcell{1}{\textbf{诚信}\\\textbf{承诺}}
		&
		\begin{minipage}[l][5cm][c]{\linewidth}\zihao{-4}
			\indent 本人郑重声明所呈交的实习报告是本人在指导教师指导下进行的研究工作及取得的研究成果。据我所知，除了文中特别加以标注的地方外，报告中不包含其他人已经发表或撰写过的研究成果。与我一同工作的同学对本文研究所做的贡献均已在报告中作了明确的说明并表示谢意。
			\vskip 0.5cm
			\raggedleft
			\textbf{学生(签名)：}\hspace{2cm}
		\end{minipage}\\
		\hline
		\multirowcell{1}{\textbf{指导}\\\textbf{教师}\\\textbf{评语}}
		&\begin{minipage}[l][8cm][c]{\linewidth}\zihao{-4}
			\begin{minipage}[l][3cm][c]{\linewidth}
				
			\end{minipage}
			
			\makebox[\linewidth][r]{\textbf{成绩评定：}\hspace{2cm}}
			\vskip 0.2cm
			\makebox[\linewidth][r]{\textbf{指导老师(签名)：}\hspace{2cm}}
			\vskip 0.2cm
			\makebox[\linewidth][r]{\textbf{年\quad 月\quad 日}\hspace{1cm}}
		\end{minipage}\\
		\hline
	\end{tabular}
\end{table}
}


\providecommand{\experienceName}[1]{
	\newpage
	\pagestyle{empty}
	\renewcommand{\arraystretch}{2}
	\begin{table}
		\centering
		\begin{tabular}{|p{0.06\linewidth}<\centering|p{0.9\linewidth}|}
			\hline
			\multirowcell{1}{\textbf{学生}\\\textbf{实验}\\\textbf{心得}}&
			\begin{minipage}[l][12cm][c]{\linewidth}
				\begin{minipage}[l][10cm][c]{\linewidth}\zihao{-4}
					#1
				\end{minipage}
				
				\makebox[\linewidth][r]{\textbf{学生(签名)：}\textit{\@xdulab@Name}\hspace{0.5cm}}
				\vskip 0.2cm
				\makebox[\linewidth][r]{\textbf{\today}\hspace{1cm}}
			\end{minipage}
			\\ \hline
			\multirowcell{1}{\textbf{诚信}\\\textbf{承诺}}
			&
			\begin{minipage}[l][5cm][c]{\linewidth}\zihao{-4}
				\indent 本人郑重声明所呈交的实习报告是本人在指导教师指导下进行的研究工作及取得的研究成果。据我所知，除了文中特别加以标注的地方外，报告中不包含其他人已经发表或撰写过的研究成果。与我一同工作的同学对本文研究所做的贡献均已在报告中作了明确的说明并表示谢意。
				\vskip 0.5cm
				\makebox[\linewidth][r]{\textbf{学生(签名)：}\textit{\@xdulab@Name}\hspace{0.5cm}}
			\end{minipage}\\
			\hline
			\multirowcell{1}{\textbf{指导}\\\textbf{教师}\\\textbf{评语}}
			&\begin{minipage}[l][8cm][c]{\linewidth}\zihao{-4}
				\begin{minipage}[l][3cm][c]{\linewidth}
					
				\end{minipage}
				
				\makebox[\linewidth][r]{\textbf{成绩评定：}\hspace{2cm}}
				\vskip 0.2cm
				\makebox[\linewidth][r]{\textbf{指导老师(签名)：}\hspace{2cm}}
				\vskip 0.2cm
				\makebox[\linewidth][r]{\textbf{年\quad 月\quad 日}\hspace{1cm}}
			\end{minipage}\\
			\hline
		\end{tabular}
	\end{table}
}

% 中文标题格式设置
% 目录深度
%\setcounter{secnumdepth}{3}
% 节标题格式, 居中, 使用\chinese命令修改计数器
%\def\@seccntformat#1{\csname the#1\endcsname\ }
%\renewcommand\thesection{\chinese{section}、}
%\renewcommand\thesubsection{\arabic{section}\thinspace.\thinspace\arabic{subsection}}
%\renewcommand\thesubsubsection{\thesubsection\thinspace.\thinspace\arabic{subsubsection}}
%\renewcommand\section{\@startsection{section}{1}{\z@}%
% 	{-3.5ex \@plus -1ex \@minus -.2ex}%
%	{2.3ex \@plus.2ex}%
%	{\centering\normalfont\Large\bfseries}}
%\renewcommand\subsection{\@startsection{subsection}{2}{\z@}%
%	{-3.25ex\@plus -1ex \@minus -.2ex}%
%	{1.5ex \@plus .2ex}%
%	{\normalfont\large\bfseries}}
%\renewcommand\subsubsection{\@startsection{subsubsection}{3}{\z@}%
%	{-3.25ex\@plus -1ex \@minus -.2ex}%
%	{1.5ex \@plus .2ex}%
%	{\normalfont\normalsize\bfseries}}
%\renewcommand\paragraph{\@startsection{paragraph}{4}{\z@}%
%	{3.25ex \@plus1ex \@minus.2ex}%
%	{-1em}%
%	{\normalfont\normalsize\bfseries}}
%\renewcommand\subparagraph{\@startsection{subparagraph}{5}{\parindent}%
%	 {3.25ex \@plus1ex \@minus .2ex}%
%	 {-1em}%
%	 {\normalfont\normalsize\bfseries}}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%%%% 封面变量
\newcommand*\course[1]{%
	\renewcommand{\@xdulab@Course}{#1}}

\newcommand*\academyname[1]{%
	\renewcommand{\@xdulab@AcademyName}{#1}}
    
\newcommand*\profession[1]{%
	\renewcommand{\@xdulab@Profession}{#1}}


\newcommand*\studentName[1]{%
	\renewcommand{\@xdulab@Name}{#1}}

\newcommand*\studentId[1]{%
	\renewcommand{\@xdulab@Number}{#1}}    

\newcommand*\teacherName[1]{%
	\renewcommand{\@xdulab@Teacher}{#1}}   

\newcommand*\location[1]{%
	\renewcommand{\@xdulab@Place}{#1}}   
    
\newcommand*\grade[1]{%
	\renewcommand{\@xdulab@Grade}{#1}}   

\newcommand*\startDate[1]{%
	\renewcommand{\@xdulab@Fisrtdate}{#1}}
    
\newcommand*\lastDate[1]{%
	\renewcommand{\@xdulab@Lastdate}{#1}}

%\newcommand*\supervisor[1]{%
%	\renewcommand{\mcm@tokens@supervisor}{#1}}
%
%\newcommand*\yearinput[1]{%
%	\renewcommand{\mcm@tokens@yearinput}{#1}}
%
%\newcommand*\monthinput[1]{%
%	\renewcommand{\mcm@tokens@monthinput}{#1}}
%
%\newcommand*\dayinput[1]{%
%	\renewcommand{\mcm@tokens@dayinput}{#1}}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%%设置目录格式
%% 节的目录格式
%\titlecontents{section}[0pt]{\heiti\vspace{2mm}\bfseries}
%{\thecontentslabel\hskip.5em}{}{\titlerule*[0.5pc]{.}\contentspage}
%% 小节的目录格式
%\titlecontents{subsection}[30pt]{\songti}
%{\thecontentslabel\hskip.5em}{}{\titlerule*[0.5pc]{.}\contentspage}
%\titlecontents{subsubsection}[55pt]{\songti}
%{\thecontentslabel\hskip.5em}{}{\titlerule*[0.5pc]{.}\contentspage}

\endinput
