<template>
  <FlexCard header-height="auto">
    <template #header>
      <div class="flex flex-row items-center justify-between w-full animate-pulse">
        <div class="flex flex-row items-center justify-between gap-3 mt-1 w-full">
          <div class="h-6 bg-auxiliar-gray rounded w-64"></div>
          <div class="h-8 bg-auxiliar-gray rounded w-8"></div>
        </div>
      </div>
    </template>
    <div class="max-w-[837px] mx-auto flex-1 w-full min-h-0">
      <div class="flex flex-col h-full gap-4 py-4 animate-pulse">
        <!-- Messages skeleton -->
        <div class="flex flex-1 min-h-0 gap-2 w-full overflow-y-auto">
          <div class="flex flex-col w-full gap-6">
            <!-- User message skeleton -->
            <div class="flex justify-end">
              <div class="w-3/4">
                <div class="h-20 bg-auxiliar-gray rounded w-full"></div>
              </div>
            </div>
            <!-- Agent message skeleton -->
            <div class="flex justify-start">
              <div class="w-3/4">
                <div class="h-20 bg-auxiliar-gray rounded w-full"></div>
              </div>
            </div>
          </div>
        </div>
        <!-- Chat input skeleton -->
        <div class="flex flex-col gap-1 p-3 relative rounded-xl border border-auxiliar-gray bg-surface shadow-sm">
          <div class="absolute top-[-.85rem] right-20 h-6 w-16 bg-auxiliar-gray rounded-full"></div>
          <div class="h-20 bg-auxiliar-gray rounded w-full"></div>
        </div>
      </div>
    </div>
  </FlexCard>
</template>

