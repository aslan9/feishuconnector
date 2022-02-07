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
    # 获取全部记录
    records = fc.get_bitable_records('wikcnlBvPJ8xoTSfVtQwGBkrUWc', 'tblGZPQYMzrwRMeo')

    # 插入全部记录
    fc.insert_bitable_records('wikcnlBvPJ8xoTSfVtQwGBkrUWc', 'tblGZPQYMzrwRMeo', records)
