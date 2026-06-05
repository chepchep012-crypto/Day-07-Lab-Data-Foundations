---
category: billing
audience: internal-support
owning_team: billing_ops
---

# Quy trình Nội bộ: Xử lý Cảnh báo Gian lận Thanh toán (Fraud Alert)

Tài liệu này CHỈ DÀNH CHO TƯ VẤN VIÊN. Tuyệt đối không tiết lộ tiêu chí quét gian lận cho khách hàng.

Khi hệ thống tự động gắn cờ rủi ro cao (Flagged as Fraud) đối với một giao dịch mua gói Premium, tài khoản người dùng sẽ bị khóa tạm thời. Tư vấn viên tiếp nhận khiếu nại thực hiện kiểm tra:

1. Truy cập vào **Stripe Dashboard**, tìm mã giao dịch (`ch_X...` hoặc `pi_X...`) được cung cấp trong ticket.
2. Kiểm tra điểm số rủi ro **Radar Score**:
   - Nếu điểm từ 75 đến 90 (Khách hàng dùng VPN hoặc đổi IP liên tục): Yêu cầu khách hàng gửi email từ chính email đăng ký tài khoản để xác nhận họ là người thực hiện giao dịch. Sau khi nhận được email xác nhận, nhấn nút **"Whitelist User"** trên hệ thống Admin.
   - Nếu điểm trên 90 hoặc hệ thống báo trùng thẻ đen (Stolen Card ID): Không tự ý mở khóa.

**Tiêu chí chuyển tiếp (Escalation):** Đối với các trường hợp điểm rủi ro trên 90 hoặc khách hàng liên tục spam yêu cầu đòi mở khóa bằng những lời lẽ đe dọa, tư vấn viên giữ nguyên trạng thái khóa và chuyển ticket thẳng cho đội **`billing_ops`** gắn nhãn "Fraud Investigation" để xử lý chuyên sâu.