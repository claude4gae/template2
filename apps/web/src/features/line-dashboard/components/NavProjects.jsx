// 파일 경로: src/features/line-dashboard/components/NavProjects.jsx
import { Folder, Forward, MoreHorizontal, Trash2 } from "lucide-react"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"

/**
 * -------------------------------------------------------------
 * NavProjects 컴포넌트
 * -------------------------------------------------------------
 * 사이드바에 "Projects" 그룹을 표시하고,
 * 각 프로젝트 항목에 "더보기" 드롭다운 메뉴를 제공한다.
 *
 * 전달 속성:
 * - projects: { name, url, icon } 형태의 프로젝트 리스트
 * -------------------------------------------------------------
 */
export function NavProjects({ projects }) {
  const { isMobile } = useSidebar()

  // projects가 배열이 아니면 빈 배열로 처리
  const projectItems = Array.isArray(projects) ? projects : []

  // 프로젝트가 하나도 없으면 아무것도 렌더링하지 않음
  if (projectItems.length === 0) return null

  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden">
      {/* 사이드바 섹션 제목 */}
      <SidebarGroupLabel>Projects</SidebarGroupLabel>

      {/* 프로젝트 리스트 */}
      <SidebarMenu>
        {projectItems.map((item) => (
          <SidebarMenuItem key={item.name}>
            {/* 프로젝트 버튼 (아이콘 + 이름) */}
            <SidebarMenuButton asChild>
              <a href={item.url}>
                {/* item.icon은 lucide-react 아이콘 컴포넌트 */}
                <item.icon />
                <span>{item.name}</span>
              </a>
            </SidebarMenuButton>

            {/* 각 프로젝트별 "더보기" 드롭다운 메뉴 */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                {/* hover 시 보이는 액션 버튼 */}
                <SidebarMenuAction showOnHover>
                  <MoreHorizontal />
                  <span className="sr-only">More</span>
                </SidebarMenuAction>
              </DropdownMenuTrigger>

              <DropdownMenuContent
                className="w-48 rounded-lg"
                // 모바일에서는 아래쪽, 데스크탑에서는 오른쪽에 열리도록 설정
                side={isMobile ? "bottom" : "right"}
                align={isMobile ? "end" : "start"}
              >
                {/* 1️⃣ 프로젝트 보기 */}
                <DropdownMenuItem>
                  <Folder className="text-muted-foreground" />
                  <span>View Project</span>
                </DropdownMenuItem>

                {/* 2️⃣ 프로젝트 공유 */}
                <DropdownMenuItem>
                  <Forward className="text-muted-foreground" />
                  <span>Share Project</span>
                </DropdownMenuItem>

                <DropdownMenuSeparator />

                {/* 3️⃣ 프로젝트 삭제 */}
                <DropdownMenuItem>
                  <Trash2 className="text-muted-foreground" />
                  <span>Delete Project</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        ))}

        {/* 추가적인 프로젝트 항목이 있을 때 사용할 "More" 버튼 */}
        <SidebarMenuItem>
          <SidebarMenuButton className="text-sidebar-foreground/70">
            <MoreHorizontal className="text-sidebar-foreground/70" />
            <span>More</span>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarGroup>
  )
}
