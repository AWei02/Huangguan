import streamlit as st
import pandas as pd


def process(input_df, sample_time, sample_mode):
    # 数据处理，根据采样时间和模式来判断
    # 采样时间【每秒:1S；每分钟:1Min；每小时:1H】
    # 采样模式【周期首个值:first；周期均值:mean；周期末值:last】
    input_df['时间'] = pd.to_datetime(input_df['时间'], format='%Y年%m月%d日 %H:%M:%S')  # 转格式
    input_df.set_index('时间', inplace=True)  # 将时间列设置为索引

    if sample_mode == '首位':
        df_resampled = input_df.resample(sample_time).first()
    elif sample_mode == '末位':
        df_resampled = input_df.resample(sample_time).last()
    else:
        df_resampled = input_df.resample(sample_time).mean()
    df_resampled.dropna(how='all', inplace=True)  # 删除一整行都没有数据的值(有时候数据是断开的)
    return df_resampled


def is_null(input_df):
    # 输出：数据个数，数据字符串，数据
    missing_data_index = input_df[input_df.isna().any(axis=1)].index
    missing_data_index_str = ', '.join(map(str, missing_data_index))
    return len(missing_data_index), missing_data_index_str, missing_data_index


@st.cache_data
def convert_df(input_df):
    return input_df.to_csv().encode('gbk')


st.set_page_config(
   page_title="数据处理工具",
   page_icon=":memo:",
   layout="wide",
   initial_sidebar_state="expanded",
)

# 边栏中创建单选按钮
st.sidebar.markdown("# :chestnut:操作步骤")
selection = st.sidebar.radio("步骤", ("1. 数据处理", "2. 绘图"), label_visibility="hidden")

# 根据选择的选项显示不同的输入组件
if selection == "1. 数据处理":
    uploaded_file = st.sidebar.file_uploader("上传EXCEL文件：", type=["xlsx"], accept_multiple_files=False)

    if uploaded_file is not None:
        # 读取上传的文件内容
        df = pd.read_excel(uploaded_file)

        num, col2 = st.sidebar.columns(2)
        input_number = num.number_input("周期：", value=1, step=1)
        selected_unit = col2.selectbox("单位", ("秒(s)", "分钟(min)", "小时(hour)"),
                                       index=1, disabled=True, label_visibility="hidden")

        unit = {"秒(s)": "S",
                "分钟(min)": "Min",
                "小时(hour)": "H"}
        sample = str(input_number) + unit[selected_unit]
        # st.write("结果:", sample)

        mode = st.sidebar.radio("模式：", ("首位", "末位", "均值"))
        # st.write("结果:", mode)

        df = process(df, sample, mode)  # 根据时间和模式采样

        # 文件导出按钮
        csv = convert_df(df)
        st.download_button(
            label="下载CSV文件",
            data=csv,
            file_name='output.csv',
            mime='text/csv',
        )

        row_visible = st.number_input(':question:想看几行:question:', value=5, step=1)

        # 在主页面展示DataFrame的前n行
        st.write("文件处理情况：")
        st.write(df.head(row_visible))

        num, war, null_df = is_null(df)  # 判断是否含缺失值
        if num != 0:
            st.warning(f"警告：数据处理后存在 {num} 个缺失值，具体为：\n{war}", icon="⚠️")
            st.write("下面展示缺失数据的详细情况（不建议导出文件绘图）：")
            st.write(df.loc[null_df])  # 展示缺失数据
        else:
            st.success(f"通过：数据处理后不存在个缺失值，请将CSV文件下载到本地后再进行绘图", icon="✅")

elif selection == "2. 绘图":
    uploaded_file = st.sidebar.file_uploader("上传CSV文件：", type=["csv"], accept_multiple_files=False)

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, index_col="时间", encoding="gbk")  # 读取
        columns = df.columns.tolist()  # 获取列名
        selected_columns = st.multiselect("选择", columns, placeholder="选择需要观察的通道", label_visibility="hidden")

        df.index = pd.to_datetime(df.index)  # index转为时间格式

        st.sidebar.write(":bulb:数据时间范围(请勿超出):")
        st.sidebar.write(f"{df.index[0]}~~{df.index[-1]}")
        # 创建侧边栏并添加起始时间和终止时间的输入框
        start_date = st.sidebar.date_input("选择起始日期", value=df.index[0])
        start_time = st.sidebar.time_input("选择起始时间", value=df.index[0])
        end_date = st.sidebar.date_input("选择终止日期", value=df.index[-1])
        end_time = st.sidebar.time_input("选择终止时间", value=df.index[-1])
        # 将起始时间和终止时间转换为datetime对象
        start_datetime = pd.to_datetime(str(start_date) + ' ' + str(start_time))
        end_datetime = pd.to_datetime(str(end_date) + ' ' + str(end_time))

        if start_datetime < end_datetime:
            if end_datetime > df.index[0] and start_datetime < df.index[-1]:
                # 根据起始时间和终止时间筛选DataFrame
                filtered_df = df.loc[start_datetime:end_datetime]

                if selected_columns:
                    filtered_df = filtered_df[selected_columns]  # 数据筛选
                    st.line_chart(filtered_df)  # 画图
                    st.write(filtered_df)  # 展示表格
            else:
                st.error(f"警告：选取时间已经超出数据时间范围({df.index[0]}-{df.index[-1]})！", icon="⚠️")
        else:
            st.error("警告：起始时间不能超过终止时间！", icon="⚠️")
