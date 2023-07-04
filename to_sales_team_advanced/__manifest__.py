{
    'name': "Sales Teams Advanced",
    'name_vi_VN': "Nhóm bán hàng nâng cao",
    'summary': """
Adding more sales access groups""",
    'summary_vi_VN': """
Thêm nhiều nhóm truy cập bán hàng""",
    'description': """
What it does
============
Businesses with a large number of sales staff will need to arrange and manage sales staff by teams and regions. From there, it is possible to monitor and plan the appropriate team development. This module is a base module, providing various groups of access rights suitable for businesses to secure relevant sales team and sales region information.

Key Features
============

**1. Reorganizes access rights group in the Sales app:**

**Access Groups**

* *Sales / User: Own Documents Only*: Default group in Odoo.
* *Sales / Sales Team Leader*: New access group, inherits access rights of the *Sales / User: Own Documents Only* group.
* *Sales / Regional Manager*: New access group, inherits access rights of the *Sales / Sales Team Leader* group.
* *Sales / User: All Documents*: Default group in Odoo, now inherits access rights of the *Sales / Regional Manager* group instead of the *Sales / User: Own Documents Only* one.
* *Sales / Administrator*: Full access to the Sales Management application.

**Security Policies**

* *Sales / User: Own Documents Only*: Create/View/Edit their own documents/data or assigned to or didn't assign to anyone;
* *Sales / Sales Team Leader*: Inherits access rights of the *Sales / User: Own Documents Only* group and extends the access to information/data of members of the team they are in charge of; or information/data that is not assigned to any team.
* *Sales / Regional Manager*: Inherits access rights of the *Sales / Sales Team Leader* group and can also access information/data of staff in the region that they are in charge of; or information/data that is not assigned to any particular region.
* *Sales / User: All Documents*: Full access for all teams except the Sales configuration.
* *Sales / Administrator*: Full access to the Sales Management application, including the configuration.

**Note:**

When this module is installed alone, without other modules such as *to_sales_team_advanced_crm* or *to_sales_team_advanced_sale*, the security policies of leads/opportunities or quotation/sales orders are not affected. Therefore, you can install this module in conjunction with:

* CRM - Sales Teams Advanced `(to_sales_team_advanced_crm) <https://viindoo.com/apps/app/15.0/to_sales_team_advanced_crm>`_ to set up the security policies for leads/opportunities.
* Sales - Sales Teams Advanced `(to_sales_team_advanced_sale) <https://viindoo.com/apps/app/15.0/to_sales_team_advanced_sale>`_ to set up the security policies for quotations/sales orders.

**2. Categorize sales teams by sales region.**

**3. Provides filter/group criteria by sales region.**

Supported Editions
==================
1. Community Edition
2. Enterprise Edition

    """,
    'description_vi_VN': """
Mô tả
=====
Các doanh nghiệp đang có lượng nhân viên bán hàng đông đảo sẽ có nhu cầu sắp xếp, quản lý nhân viên bán hàng theo các đội, các khu vực. Từ đó có thể theo dõi và lập kế hoạch phát triển đội nhóm phù hợp. Mô-đun này là mô-đun cơ sở, cung cấp tính năng phân cấp quyền truy cập theo các cấp phù hợp hơn cho doanh nghiệp nhằm bảo mật thông tin liên quan theo từng đội nhóm, khu vực.

Tính năng nổi bật
=================

**1. Sắp xếp lại các nhóm phân quyền trong ứng dụng Bán hàng**

**Nhóm truy cập**

* *Bán hàng/Người dùng: Chỉ tài liệu của chính mình*: Đây là nhóm mặc định trong Odoo.
* *Bán hàng/Trưởng đội bán hàng*: Nhóm truy cập mới kế thừa nhóm Bán hàng/Người dùng: Chỉ tài liệu của chính mình.
* *Bán hàng/Giám đốc khu vực*: Nhóm truy cập mới kế thừa nhóm Bán hàng/Đội trưởng bán hàng.
* *Bán hàng/Người dùng: Tất cả tài liệu*: Đây là nhóm mặc định trong Odoo. Bây giờ nó kế thừa Bán hàng/Người quản lý khu vực thay vì Bán hàng/Người dùng: Chỉ tài liệu của chính mình.
* *Bán hàng/Quản trị viên*: Đầy đủ quyền truy cập đến ứng dụng Quản lý bán hàng.

**Chính sách bảo mật**

* *Bán hàng/Người dùng: Chỉ tài liệu của chính mình*: Tạo/xem/sửa được các thông tin/dữ liệu/báo cáo do mình tạo hoặc được phân công cho mình hoặc không được phân công cho nhân viên nào;
* *Bán hàng/Trưởng đội bán hàng*: Kế thừa các quyền của *Bán hàng/Người dùng: Chỉ tài liệu của chính mình*, đồng thời được mở rộng quyền với nhân viên trong đội mình phụ trách; hoặc không thuộc phụ trách của đội nào.
* *Bán hàng/Giám đốc khu vực*: Kế thừa các quyền của *Bán hàng/Trưởng đội bán hàng*, đồng thời được mở rộng quyền với nhân viên trong khu vực mình phụ trách; hoặc không thuộc phụ trách của khu vực nào.
* *Bán hàng/Người dùng: Tất cả tài liệu*: Có đầy đủ quyền, trừ quyền cấu hình;
* *Bán hàng/Quản trị viên*: Có đầy đủ quyền bao gồm cả phần cấu hình.
   
**Lưu ý:**

Mô-đun này khi được cài đặt lên và chưa kết hợp với các mô-đun khác như *to_sales_team_advanced_crm* hay *to_sales_team_advanced_sale* thì sẽ chưa có ảnh hưởng tới chính sách bảo mật của tiềm năng/cơ hội hay báo giá/đơn bán. Vì vậy, tùy vào nghiệp vụ, bạn có thể cài đặt mô-đun này kèm với:

* Mô-đun CRM - Đội bán hàng nâng cao `(to_sales_team_advanced_crm) <https://viindoo.com/vi/apps/app/15.0/to_sales_team_advanced_crm>`_ để phân quyền chính sách bảo mật truy cập các tiềm năng/cơ hội.
* Mô-đun Bán hàng - Đội bán hàng nâng cao `(to_sales_team_advanced_sale) <https://viindoo.com/vi/apps/app/15.0/to_sales_team_advanced_sale>`_ để phân quyền chính sách bảo mật truy cập các báo giá/bán hàng.

**2. Phân chia đội bán hàng theo khu vực bán hàng.**

**3. Xây dựng bộ lọc/nhóm theo khu vực bán hàng.**

Ấn bản được hỗ trợ
==================
1. Ấn bản Community
2. Ấn bản Enterprise

    """,
    'images':['images/main_screenshot.png'],
    'author': "T.V.T Marine Automation (aka TVTMA),Viindoo",
    'website': 'https://viindoo.com/apps/app/15.0/to_sales_team_advanced',
    'live_test_url': "https://v15demo-int.viindoo.com",
    'live_test_url_vi_VN': "https://v15demo-vn.viindoo.com",
    'demo_video_url': "https://youtu.be/EWov_3MkJIw",
    'support': 'apps.support@viindoo.com',

    'category': 'Sales',
    'version': '1.0.1',

    # any module necessary for this one to work correctly
    'depends': ['sales_team','account_accountant','account_followup'],

    # always loaded
    'data': [
        'security/sales_team_security.xml',
        'security/ir.model.access.csv',
        'views/crm_team_region_views.xml',
        'views/crm_team_views.xml',
    ],
    'images' : ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 45.9,
    'currency': 'EUR',
    'license': 'OPL-1',
}
