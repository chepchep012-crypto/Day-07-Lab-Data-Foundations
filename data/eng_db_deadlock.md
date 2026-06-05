---
category: service_limits
audience: engineering-only
owning_team: core_eng
---

# Tài liệu Xử lý Sự cố Kỹ thuật: Lỗi Kẹt DB Deadlock Khi Cập Nhật Hạn Mức Ghế (Seat Allocation)

Tài liệu bảo mật - Chỉ dành cho Kỹ sư Hệ thống hệ Core.

Khi doanh nghiệp lớn (Enterprise) thực hiện mua thêm ghế cho nhân viên với số lượng lớn (>100 ghế đồng thời), Core DB có thể dính lỗi `PostgreSQL Deadlock Detected` trên bảng `organization_seats`, dẫn đến việc hệ thống treo và báo lỗi "Service Limitations" trên frontend của khách hàng.

Quy trình giải cứu dữ liệu:
1. Đăng nhập vào RDS PostgreSQL Instance qua công cụ quản lý bảo mật.
2. Chạy câu lệnh truy vấn sau để tìm các tiến trình (PIDs) đang gây nghẽn mạch khóa (Lock):
   `SELECT blocked_locks.pid AS blocked_pid, blocking_locks.pid AS blocking_pid FROM pg_catalog.pg_locks...`
3. Tiến hành giải phóng bộ nhớ bằng cách kill tiến trình chiếm quyền khóa lâu nhất: `SELECT pg_terminate_backend(blocking_pid);`
4. Sau khi giải phóng, chạy script patch database để tái cấu trúc hàng đợi xếp hàng: `ansible-playbook -i inventory/prod deploy_seat_patch.yml`.

Nếu sau khi chạy lệnh terminate mà CPU của RDS vẫn duy trì ở mức >95%, lập tức kích hoạt hạ tầng dự phòng (Failover) và thông báo lên kênh `#eng-incidents` trạng thái SEV-1.