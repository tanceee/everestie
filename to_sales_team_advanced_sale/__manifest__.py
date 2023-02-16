{
    'name': "Sales - Sales Teams Advanced",
    'name_vi_VN': "Bán hàng - Đội bán hàng nâng cao",
    'summary': """
Integrate Sales application with Sales Teams Advanced""",
    'summary_vi_VN': """
Tích hợp ứng dụng Bán hàng với Đội bán hàng nâng cao""",
    'description': """
What it does
============

This module integrates the Sales Management app (sale_management) and the Sales Team Advanced `(to_sales_team_advanced) <https://viindoo.com/vi/apps/app/15.0/to_sales_team_advanced>`_ to allocate sales teams by region and set up adequate security policies to access quotations/sales orders, reports, etc. in the Sales app.

Key Features
============

#. Improve Sales app access rights:

   * **Sales / User: Own Documents Only**: Create/view/edit information/data created by themselves or are assigned to them, or those that are unassigned.
   * **Sales / Sales Team Leader**: Create/view/edit information/data of quotations/sales orders, reports:

     * Created by themselves or assigned to them; 
     * Of the team members that they are in charge of;
     * Of the team that they are in charge of (information/data might not be assigned to anyone in particular but still belongs to their team); 
     * Or information/data that is not assigned to any team.

   * **Sales / Regional Manager**: Create/view/edit information/data of quotations/sales orders, reports:

     * Created by themselves or assigned to them; 
     * Of the staff that they are in charge of;
     * Of the region that they are in charge of; 
     * Or information/data that is not assigned to any team.

   * **Sales / User: All Documents**: Full access for all teams except the Sales configuration.
   * **Sales / Administrator**: Full access to the Sales Management application, including the configuration.

#. Add Sales Region, Team Leader, and Regional Manager fields on the quotations/sales orders.
#. Add filter and grouping criteria such as Sales Region, Team Leader, and Regional Manager on the list view of quotations/sales orders, sales reports, and customer invoices/vendor bills.
#. Add a configuration menu for the sales region in **Sales ‣ Configuration ‣ Sales Region**.

Supported Editions
==================
1. Community Edition
2. Enterprise Edition

    """,

    'description_vi_VN': """
Mô tả
=====
Đây là mô-đun liên kết giữa Ứng dụng Bán hàng (sale_management) và mô-đun Nhóm bán hàng nâng cao `(to_sales_team_advanced) <https://viindoo.com/vi/apps/app/15.0/to_sales_team_advanced>`_ với mục đích phân chia đội bán hàng theo các khu vực và phân quyền truy cập/phân quyền bảo mật thông tin về báo giá/đơn bán, báo cáo,... phù hợp trong ứng dụng Bán hàng.

Tính năng nổi bật
=================
#. Cải thiện quyền truy cập của ứng dụng Bán hàng:

   * **Bán hàng/Người dùng: Chỉ tài liệu của chính mình**: Tạo/xem/sửa được các thông tin/dữ liệu báo giá/đơn bán do mình tạo hoặc được phân công cho mình hoặc không được phân công cho nhân viên nào;
   * **Bán hàng/Trưởng đội bán hàng**: Tạo/xem/sửa các thông tin/dữ liệu báo giá/đơn bán, báo cáo:
   
     * Của mình tạo hoặc được phân công cho mình;
     * Của nhân viên trong đội mình phụ trách;
     * Của đội mình phụ trách (không được phân công cho nhân viên nào nhưng vẫn thuộc đội mình);
     * Hoặc không thuộc phụ trách của đội nào.
     
   * **Bán hàng/Giám đốc khu vực**: Tạo/xem/sửa các thông tin/dữ liệu báo giá/đơn bán, báo cáo:
   
     * Của mình tạo hoặc được phân công cho mình;
     * Của nhân viên trong khu vực mình phụ trách;
     * Của khu vực mình phụ trách;
     * Hoặc không thuộc phụ trách của khu vực nào.
        
   * **Bán hàng/Người dùng: Tất cả tài liệu**: Có đầy đủ quyền, trừ quyền cấu hình ứng dụng;
   * **Bán hàng/Quản trị viên**: Có đầy đủ quyền bao gồm cả phần cấu hình trong ứng dụng.

#. Thêm trường thông tin về Khu vực Bán hàng, Đội trưởng và Giám đốc khu vực trên báo giá/đơn bán.
#. Thêm các bộ lọc và nhóm theo với tiêu chí Khu vực bán hàng, Đội trưởng bán hàng, Quản lý khu vực bán hàng tại các giao diện Báo giá/Đơn bán, Báo cáo bán hàng & Hóa đơn khách hàng/nhà cung cấp.
#. Thêm menu cấu hình về Khu vực bán hàng trong ứng dụng **Bán hàng ‣ Cấu hình ‣ Khu vực bán hàng**.

Ấn bản được hỗ trợ
==================
1. Ấn bản Community
2. Ấn bản Enterprise

    """,

    'author': "T.V.T Marine Automation (aka TVTMA),Viindoo",
    'website': 'https://viindoo.com/apps/app/15.0/to_sales_team_advanced_sale',
    'live_test_url': "https://v15demo-int.viindoo.com",
    'live_test_url_vi_VN': "https://v15demo-vn.viindoo.com",
    'demo_video_url': "https://youtu.be/LXHsmZC1YBs",
    'support': 'apps.support@viindoo.com',

    'category': 'Sales',
    'version': '1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['to_sales_team_advanced', 'sale'],

    # always loaded
    'data': [
        'security/sale_security.xml',
        'security/ir.model.access.csv',
        'report/invoice_report_views.xml',
        'report/sale_report_views.xml',
        'views/account_invoice_views.xml',
        'views/crm_team_region_views.xml',
        'views/sale_order_views.xml',
        'views/root_menu.xml'
    ],
    'images' : ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'auto_install': True,
    'uninstall_hook': 'uninstall_hook',
    'price': 49.9,
    'currency': 'EUR',
    'license': 'OPL-1',
}
