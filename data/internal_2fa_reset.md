---
category: password_recovery
audience: internal-support
owning_team: core_eng
---

# Quy trình Bảo mật Nội bộ: Reset Xác thực 2 Yếu tố (2FA) cho Khách hàng

Tài liệu mật - Chỉ lưu hành nội bộ trong bộ phận Hỗ trợ khách hàng.

Khi khách hàng bị mất thiết bị điện thoại chứa ứng dụng OTP và yêu cầu tắt xác thực 2 yếu tố (2FA) để khôi phục quyền truy cập:

1. **Yêu cầu bắt buộc:** Tư vấn viên phải yêu cầu khách hàng cung cấp ảnh chụp CMND/CCCD hoặc Hộ chiếu trùng khớp với tên đăng ký trên tài khoản để xác minh danh tính.
2. Sau khi xác minh thành công, truy cập vào công cụ bảo mật nội bộ **SecTools dashboard**.
3. Tra cứu bằng ID người dùng, tìm mục **MFA Settings** và nhấp vào nút đỏ **"Disable 2FA Override"**.
4. Hệ thống sẽ tự động gửi một email thông báo "2FA đã bị tắt" đến hộp thư của user. Hướng dẫn khách hàng đăng nhập lại bằng mật khẩu gốc và thiết lập lại 2FA ngay lập tức.

**Tiêu chí chuyển tiếp (Escalation):** Nếu kiểm tra tab **Security Audit Logs** của user thấy có hơn 5 lần nhập sai mã OTP liên tiếp từ các địa chỉ IP nước ngoài khác nhau trong vòng 1 giờ, hãy ĐÓNG BĂNG tài khoản tạm thời và chuyển ngay thông tin cho đội `core_eng` để điều tra hành vi tấn công dò mã (brute-force).