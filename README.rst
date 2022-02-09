飞书文档内容连接器

install::

    pip install feishuconnector


code usage::

    from feishuconnector import FeishuConnector

    fc = FeishuConnector()
    fc.init("user***", "pass***)

实际使用的流程：

在多维表格的编辑页面，url一般是这样的：https://puyuan.feishu.cn/wiki/wikcnlBvPJ8xoTSfVtQwGBkrUWc?table=tblGZPQYMzrwRMeo&view=vewWhDJdAM, 注意提取其中 node_token=wikcnlBvPJ8xoTSfVtQwGBkrUWc, table_id=tblGZPQYMzrwRMeo

调用如下::


    from feishuconnector import FeishuConnector

    fc = FeishuConnector()
    fc.init("user***", "pass***)
    # 获取多维表格全部记录
    records = fc.get_bitable_records('wikcnlBvPJ8xoTSfVtQwGBkrUWc', 'tblGZPQYMzrwRMeo')

    # 在多维表格中插入记录
    fc.insert_bitable_records('wikcnlBvPJ8xoTSfVtQwGBkrUWc', 'tblGZPQYMzrwRMeo', records)

    # 获取普通表格某range的全部数据，values is a list(rows) of list(cols)
    values = fc.get_sheet_data("wikcnQgBgZCWUx7w6ZpzzLXX3bc", "e792af")
    
    # 在普通表格中追加数据
    fc.append_sheet_data("wikcnQgBgZCWUx7w6ZpzzLXX3bc", "e792af", values)