import { useTheme } from '@/lib/theme'

import { HeroIntroSection } from './sections/HeroIntroSection'
import { HeroNetworkSection } from './sections/HeroNetworkSection'

const HeroSection = () => {
  const { theme = 'system', systemTheme } = useTheme()
  const resolvedTheme = theme === 'system' ? systemTheme : theme
  const videoSrc = resolvedTheme === 'dark' ? 'assets/video2.mp4' : 'assets/video.mp4'

  return (
    <section className='w-full overflow-hidden py-12 sm:py-8 lg:py-8'>
      <div className='mx-auto flex max-w-7xl flex-col items-center gap-8 px-4 sm:gap-16 sm:px-6 lg:gap-12 lg:px-8'>
        <HeroIntroSection />
        <HeroNetworkSection videoSrc={videoSrc} />
      </div>
    </section>
  )
}

export default HeroSection
