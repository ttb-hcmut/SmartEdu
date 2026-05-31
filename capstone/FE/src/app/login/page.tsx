import { AuthFrame } from "@/components/auth/AuthFrame"
import { LoginForm } from "@/components/auth/LoginForm"

export const metadata = {
  title: "Đăng nhập — SmartEdu",
}

export default function LoginPage() {
  return (
    <AuthFrame
      heading="Chào mừng trở lại"
      subheading="Đăng nhập để tiếp tục phiên học tập của bạn với trợ lý AI."
    >
      <LoginForm />
    </AuthFrame>
  )
}
