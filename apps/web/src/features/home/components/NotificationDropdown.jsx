import { Fragment } from 'react'
import { SettingsIcon, XIcon, LinkIcon } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { buildProfileImageUrl } from '@/lib/profileImage'
import { cn } from '@/lib/utils'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuItem
} from '@/components/ui/dropdown-menu'

const TAB_TRIGGER_CLASS_NAME =
  'data-[state=active]:!border-b-primary rounded-none border-b-2 border-b-transparent font-normal data-[state=active]:bg-transparent data-[state=active]:shadow-none dark:data-[state=active]:border-transparent dark:data-[state=active]:bg-transparent'
const NOTIFICATION_ITEM_CLASS_NAME = 'gap-3 px-2 py-3 text-base'
const NOTIFICATION_META_CLASS_NAME = 'text-muted-foreground text-sm'

const NOTIFICATION_TABS = [
  { value: 'inbox', label: 'Inbox' },
  { value: 'general', label: 'General' },
]

const NOTIFICATIONS = {
  inbox: [
    {
      avatarId: 'mark.bush',
      fallback: 'MB',
      title: 'Mark Bush',
      time: '12 Minutes ago',
      type: 'New post',
      unread: true,
    },
    {
      avatarId: 'aaron.black',
      fallback: 'AB',
      title: 'Aaron Black',
      time: '27 Minutes ago',
      type: 'New comment',
      unread: true,
    },
    {
      avatarId: 'anna',
      fallback: 'A',
      title: 'Anna has applied to create an ad for your campaign',
      time: '2 hours ago',
      type: 'New request for campaign',
      actions: true,
    },
    {
      avatarId: 'jason',
      fallback: 'J',
      title: 'Jason attached the file',
      time: '6 hours ago',
      type: 'Attached files',
      attachment: 'Work examples.com',
    },
  ],
  general: [
    {
      avatarId: 'fred.campbell',
      fallback: 'FC',
      title: 'Fred Campbell',
      time: '39 Minutes ago',
      type: 'New comment',
      unread: true,
    },
    {
      avatarId: 'scott',
      fallback: 'S',
      title: 'Scott attached the file',
      time: '3 hours ago',
      type: 'Attached files',
      attachment: 'Work examples.com',
    },
    {
      avatarId: 'harold.larson',
      fallback: 'HL',
      title: 'Harold Larson',
      time: '5 hours ago',
      type: 'New post',
      unread: true,
    },
    {
      avatarId: 'rosie',
      fallback: 'R',
      title: 'Rosie has applied to create an ad for your campaign',
      time: '8 hours ago',
      type: 'New request for campaign',
      actions: true,
    },
  ],
}

function NotificationMeta({ time, type }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className={NOTIFICATION_META_CLASS_NAME}>{time}</span>
      <div className="bg-muted size-1.5 rounded-full" />
      <span className={NOTIFICATION_META_CLASS_NAME}>{type}</span>
    </div>
  )
}

function NotificationActions() {
  return (
    <div className="mt-3 flex items-center gap-4">
      <Button variant="secondary" size="sm">
        Decline
      </Button>
      <Button size="sm">Accept</Button>
    </div>
  )
}

function NotificationAttachment({ label }) {
  return (
    <div className="mt-3 flex items-center gap-1.5">
      <LinkIcon className="text-foreground" />
      <span className="text-sm">{label}</span>
    </div>
  )
}

function UnreadIndicator() {
  return (
    <div className="flex flex-col items-center gap-3">
      <XIcon className="text-foreground size-3.5" />
      <div className="bg-primary size-1.5 rounded-full" />
    </div>
  )
}

function NotificationItem({ notification }) {
  const hasInlineContent = notification.actions || notification.attachment

  return (
    <DropdownMenuItem
      className={cn(NOTIFICATION_ITEM_CLASS_NAME, hasInlineContent && 'items-start')}
    >
      <Avatar className="size-9.5">
        <AvatarImage
          src={buildProfileImageUrl(notification.avatarId) || undefined}
          alt={notification.title}
        />
        <AvatarFallback>{notification.fallback}</AvatarFallback>
      </Avatar>
      <div className="flex w-full flex-col items-start">
        <span className="text-base font-medium">{notification.title}</span>
        <NotificationMeta time={notification.time} type={notification.type} />
        {notification.actions ? <NotificationActions /> : null}
        {notification.attachment ? (
          <NotificationAttachment label={notification.attachment} />
        ) : null}
      </div>
      {notification.unread ? <UnreadIndicator /> : null}
    </DropdownMenuItem>
  )
}

function NotificationList({ items }) {
  return items.map((notification, index) => (
    <Fragment key={`${notification.avatarId}-${notification.time}`}>
      {index > 0 ? <DropdownMenuSeparator /> : null}
      <NotificationItem notification={notification} />
    </Fragment>
  ))
}

const NotificationDropdown = ({
  trigger,
  defaultOpen,
  align = 'end'
}) => {
  return (
    <DropdownMenu defaultOpen={defaultOpen}>
      <DropdownMenuTrigger asChild>{trigger}</DropdownMenuTrigger>
      <DropdownMenuContent className='max-w-xs sm:max-w-122' align={align}>
        <Tabs defaultValue='inbox' className='gap-0'>
          <DropdownMenuLabel className='flex flex-col pb-0'>
            <div className='flex items-center justify-between gap-6 pb-2.5'>
              <span className='text-muted-foreground text-base font-normal uppercase'>Notifications</span>
              <Badge variant='secondary' className='bg-primary/10 text-primary font-normal'>
                8 New
              </Badge>
            </div>
            <div className='-mb-0.5 flex items-center justify-between gap-4'>
              <TabsList className='relative h-fit rounded-none bg-transparent p-0'>
                {NOTIFICATION_TABS.map((tab) => (
                  <TabsTrigger
                    key={tab.value}
                    value={tab.value}
                    className={TAB_TRIGGER_CLASS_NAME}
                  >
                    {tab.label}
                  </TabsTrigger>
                ))}
              </TabsList>
              <SettingsIcon className='size-5' />
            </div>
          </DropdownMenuLabel>

          <DropdownMenuSeparator className='mt-0 h-0.5' />

          {NOTIFICATION_TABS.map((tab) => (
            <TabsContent key={tab.value} value={tab.value}>
              <NotificationList items={NOTIFICATIONS[tab.value]} />
            </TabsContent>
          ))}
        </Tabs>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export default NotificationDropdown
