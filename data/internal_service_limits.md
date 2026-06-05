---
category: service_limits
audience: internal-support
owning_team: billing_ops
---

# Quy trình Nội bộ: Xử lý Lỗi Hạn mức Tài khoản (Kẹt số lượng Dự án)

Tài liệu này CHỈ DÀNH CHO TƯ VẤN VIÊN. Không gửi trực tiếp cho khách hàng.

Trường hợp khách hàng phản ánh đã trả tiền nâng cấp gói Premium thành công nhưng hệ thống vẫn báo lỗi: "Hạn mức dự án đã đạt tối đa (Max limit reached)", tư vấn viên xử lý như sau:

1. Truy cập vào công cụ nội bộ **Admin Portal (URL: admin.internal.ai)**.
2. Nhập Email của khách hàng vào thanh tìm kiếm toàn cục để mở trang **User Detail**.
3. Cuộn xuống phần **Subscription State**, kiểm tra biến `plan_type`:
   - Nếu hiển thị là `free_tier`: Giao dịch thanh toán chưa được đồng bộ sang DB người dùng. Tiến hành nhấn nút **"Force Sync Subscription"** ở góc phải.
   - Nếu hiển thị là `premium_tier` nhưng biến `max_projects_allowed` vẫn bằng 3: Đây là lỗi ghi đè dữ liệu cấu hình.

**Tiêu chí chuyển tiếp (Escalation):** Nếu sau khi nhấn "Force Sync" mà trạng thái không đổi, hoặc biến cấu hình bị kẹt, hãy chụp lại màn hình Admin Portal và tạo ticket chuyển cho đội `billing_ops` để họ can thiệp SQL thủ công.