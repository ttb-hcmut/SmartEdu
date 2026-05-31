import { AuthFrame } from "@/components/auth/AuthFrame"
import { RegisterForm } from "@/components/auth/RegisterForm"

export const metadata = {
  title: "Đăng ký — SmartEdu",
}

export default function RegisterPage() {
  return (
    <AuthFrame
      heading="Bắt đầu học tập"
      subheading="Tạo tài khoản để truy cập trợ lý giảng dạy AI của SmartEdu."
    >
      <RegisterForm />
    </AuthFrame>
  )
}
